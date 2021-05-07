import sqlite3, re, json, string
# just put in lowercase for consonants
consonants = {'B': 'b',
              'CH': 'ch',
              'D': 'd',
              'DH': 'd',
              'F': 'f',
              'G': 'g',
              'HH': 'h',
              'JH': 'zj',
              'K': 'k',
              'L': 'l',
              'M': 'm',
              'N': 'n',
              'NG': 'ng',
              'P': 'p',
              'R': 'r',
              'S': 's',
              'SH': 'sh',
              'T': 't',
              'TH': 'f',
              'V': 'f',
              'W': 'w',
              'Y': 'j',
              'Z': 's',
              'ZH': 'sh'
              }
end_conses = {'B': 'p',
              'CH': 'cj',
              'D': 't',
              'F': 'f',
              'G': 'k',
              # 'JH': 'zj',
              'K': 'k',
              'L': '',
              'M': 'm',
              'N': 'n',
              'NG': 'ng',
              'P': 'p',
              'S': 's',
              'T': 't',
              'TH': 'f',
              'Z': 's'}
# AA R => aa, but AE R => e aa
# faster => faaas toe
# beast => bist
vowels = {'AA': 'aa',
         'AE': 'e',
         'AH': 'a',
         'AO': 'o', # AO L => o small
         'AW': 'aau',
         'AY': 'aai', # exception: AY T => ait (e.g. night)
         'EH': 'e',
         'ER': 'oe', # aa if last mark
         'EY': 'ei',
         'IH': 'i',
         'IY': 'i',
         'OW': 'ou',
         'OY': 'oi',
         'UH': 'u',
         'UW': 'u'}
# append to vowel if next is m, n, ng, p, t, k, b, d or g,
special_cases = {
    'AE L': 'eu',
    'AA R': 'aa',
    'AW T': 'aut'
}

devoice = {'b': 'p', 'd': 't', 'g': 'k'}
# every syllable is [C]V(C)

def word_to_jyutping(s, cur_cmu=None, debug=False):
    locally_open_cmu = False
    if cur_cmu is None:
        con_cmu = sqlite3.connect('cmudict.db')
        cur_cmu = con_cmu.cursor()
        locally_open_cmu = True
    assert cur_cmu is not None
    # attempts to convert a single english word to jcz using the cmud database
    # input should only be ASCII, and should not have spaces
    # if nothing is found, the input falls through
    if ' ' in s:
        return s                # falls through
    try:
        s.encode('ascii')
    except:
        return s                # falls through
    # try to look in cmudict
    cur_cmu.execute('SELECT pronunciation FROM dictionary WHERE word LIKE ?', (s,))
    p = cur_cmu.fetchone()
    if p is None:
      return None
    p = p[0]
    # now start to match the pronunciation
    # clean up the pronunciation of numbers (the emphasis marks)
    p = re.sub('\d+', '', p)
    split = p.split(' ')
    if debug:
      print(split)
    i = 0
    outs = []
    syllable = ''
    carry_w = False
    carry_r = False
    # carry_j = False
    while i < len(split):
      if carry_r:
        syllable += "r"
        carry_r = False
      if carry_w:
        syllable += "w"
        carry_w = False
      curr_consts = ""
      # if carry_j:
      #   syllable += "j"
      #   carry_j = False
      # curr_consts = ""

      while split[i] in consonants:
        if i == 0 and split[0] == 'V':
          curr_consts += 'v'
        else:
          curr_consts += consonants[split[i]]
        i += 1
        if i == len(split):
          if curr_consts[0] == 'r':
            if curr_consts[1:] in devoice:
              outs.append('aa'+devoice[curr_consts[1:]])
            else:
              outs.append('aa'+curr_consts[1:])
          elif len(curr_consts) == 1:
            outs[-1] += curr_consts
          else:
            outs.append(curr_consts)
          return outs
      if curr_consts == 'th':
        curr_consts = 'd'

      if len(curr_consts) > 1 and curr_consts[0] == 'r':
        outs.append('aa')
        curr_consts = curr_consts[1:]

      if len(curr_consts) > 2 and curr_consts[0:2] in {'sh','ch','zh','sj','zj','cj'}:
        outs.append(curr_consts[0:2])
        curr_consts = curr_consts[2:]

      syllable += curr_consts

      # split[i] is a vowel
      if split[i] == 'ER' and i == len(split) - 1:
        vowel = 'aa'
      else:
        vowel = vowels[split[i]]
      other_bit = ""

      if i+1 < len(split) and split[i] == 'ER' and split[i+1] in vowels:
        carry_r = True

      # if i+1 < len(split) and split[i] == 'IY' and split[i+1] in vowels: # reinforcement vs rearrangement
      #   carry_j = True

      if i > 0 and i+1 < len(split) and split[i] in 'AH' and split[i+1] == 'L':
        # i==0: alacrity
        if i > 1 and  split[i-1] == 'Y':
          # calculator
          syllable = syllable[:-1] + 'i'
          vowel = 'u'
          i += 1
        elif i == len(split)-2:
          # technical
          vowel = 'ou'
          i += 2
        else:
          vowel = 'a'
          i += 1
      elif split[i] == 'EH' and split[i+1] == 'L' and split[i+2] in consonants:
        vowel = 'eu'
        i += 2
      elif split[i-1] == 'Y' and split[i] == 'UW':
        syllable = syllable[:-1] + "i"
        vowel = 'u'
        i += 1
      elif i+2 < len(split) and split[i] == 'AE' and split[i+1] == 'P' and split[i+2] in vowels:
        vowel = 'ep'
        i += 1
      elif i+2 < len(split) and split[i] == 'AE' and split[i+1] in {'G','K'} and split[i+2] == 'L':
        other_bit = 'k'
        i += 2
      elif split[i] == 'AW' and split[i+1] in vowels:
        i += 1
        carry_w = True
      elif i+1 < len(split) and split[i] == 'AO' and split[i+1] == 'R':
        vowel = 'o'
        if i+2 < len(split) and split[i+2] in end_conses and split[i+2] != 'G': # organic
          other_bit = end_conses[split[i+2]]
          if split[i+2] in {'S','D'}:
            i += 1
          # i += 1
        i += 2
      elif i+1 < len(split) and split[i]+' '+split[i+1] in special_cases:
        vowel = special_cases[split[i]+' '+split[i+1]]
        i += 2
      else:
        if i+2 < len(split) and split[i+1] in {'B','G','P','K'} \
        and split[i+2] in {'W','Y','L','R'}:
          other_bit = end_conses[split[i+1]]
          if split[i+1] == 'B' and split[i+2] == 'W':
            i += 2
          else:
            i += 1
        elif i+1 < len(split) and split[i][-1] == 'H' and split[i+1] in end_conses:
          other_bit = end_conses[split[i+1]]
          if i+2 < len(split) and split[i+2] in vowels:
            i += 1
          elif i+2 < len(split) and split[i+2] == 'Y':
            i += 1
          else:
            i += 2
        elif i+1 < len(split) and split[i+1] in end_conses:
          if split[i] == 'AY' and split[i+1] in {'P','T','K'}:
            vowel = 'ai' # hike is haik not haaik
            i += 1
          elif split[i] in vowels and split[i+1] in {'N', 'M', 'T'}:
            vowel = vowels[split[i]]
            if split[i+1] in {'N', 'M'} and i+1 != len(split) - 1 and split[i+2] in vowels.keys() | {'Y'}:
              if split[i] == 'AA':
                vowel += end_conses[split[i+1]]
            elif not (split[i] in {'AW', 'AY', 'EY', 'OW', 'OY'} and split[i+1] == 'T'): # dipthongs, makes things sound more cantonese
              vowel += end_conses[split[i+1]]
            if i+2 < len(split) and split[i+2] in vowels.keys() | {'Y'}:
              other_bit = ''
              i += 1
            else:
              i += 2 # skip N/M/T as next onset
          elif i+2 < len(split) and split[i+2] in vowels:
            # other_bit = end_conses[split[i+1]]
            i += 1
          elif i+2 < len(split) and split[i+2] in 'R': # {'W','Y','L','R'}
            other_bit = end_conses[split[i+1]]
            i += 1
          else:
            other_bit = end_conses[split[i+1]]
            i += 2
        else:
          i += 1


      #further adjustment
      # now len(split)-2 is N/K and i=len(split)-1 is T
      if (i == len(split)-1 or (i+1 < len(split) and split[i+1] in consonants)) and split[i-1] in {'N','K'} and split[i] in {'T','D'}:
        # skip the T as well
        i += 1
      elif i+1 < len(split) and split[i] == 'P' and split[i+1] in consonants \
            and split[i+1] not in {'W','Y','L','R'}:
        # split[i+1] cannot be semivowel W/Y
        # skip the P
        i += 1
      elif i < len(split) and split[i-1] == 'NG' and split[i] == 'K':
        i += 1
        # skip the K
      if i + 1 < len(split) and vowel != "" and other_bit != "" and \
          split[i] in {'S','Z'} and split[i+1] in consonants.keys() - {'Y'}:
        other_bit += 's'
        if split[i+1] not in {'P','B'}:
          i += 1

      syllable += vowel
      syllable += other_bit
      outs.append(syllable)
      syllable = ""

      if locally_open_cmu:
        con_cmu.close()
    return outs
