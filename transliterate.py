import sys
import ToJyutping
import pycantonese as pc
import sqlite3
import wordsegment
from words_to_jyutping import word_to_jyutping
from mouth_radicals import mouth_list

## TODO: add option to use 改革漢字, e.g. for 哋
## TODO: add option for further cantonification of English pronunciations

puncs = '，！？：；（）［］【】。「」、‧《》〈〉'
# define all of the components
onsets = {'b': '比', 'p': '并', 'm': '文', 'f': '夫', 'd': '大', 't': '天',
          'n': '乃', 'l': '力', 'z': '止', 'c': '此', 's': '厶', 'j': '央',
          'g': '丩', 'k': '臼', 'h': '亾', 'ng': '爻', 'gw': '古', 'kw': '夸',
          'w': '禾', None: '', '': ''}
finals = {'aa':'乍', 'aai':'介', 'aau':'丂', 'aam':'彡', 'aan':'万',
          'aang':'生', 'aap':'甲', 'aat':'压', 'aak':'百', 'ai':'兮', 'au':'久',
          'am':'今', 'an':'云', 'ang':'亙', 'ap':'十', 'at':'乜', 'ak':'仄',
          'e':'旡', 'ei':'丌', 'eu':'了', 'em':'壬', 'en':'円', 'eng':'正',
          'ep':'夾', 'et':'叐', 'ek':'尺', 'i':'子', 'iu':'么', 'im':'欠',
          'in':'千', 'ing':'丁', 'ip':'頁', 'it':'必', 'ik':'夕', 'o':'个',
          'oi':'丐', 'ou':'冇', 'on':'干', 'ong':'王', 'ot':'匃', 'ok':'乇',
          'u':'乎', 'ui':'会', 'un':'本', 'ung':'工', 'ut':'末', 'uk':'玉',
          'oe':'居', 'oeng':'丈', 'oek':'勺', 'eoi':'句', 'eon':'卂', 'eot':'𥘅',
          'yu':'仒', 'yun':'元', 'yut':'乙', 'ng': '爻', None: '', '': ''}
tones = {'2': '´', '3': '`', '5': '˝', '6': 'ﾞ', None: '', '':''}
syllabics = {'ng': '五`', 'm': '五.'}

def get_hex_dict(file_loc, ng_tilde=False):
    # Note: "tilde" is supposed to mean tick here
    hex_dict = {'々': '々'}
    with open(file_loc) as file:
        for line in file.read().splitlines():
            hex_str, chars = line.split(" ")
            chars = chars.replace("oe","居")
            hex_dict[chars] = chr(int(hex_str, 16))
    if ng_tilde:
        hex_dict['五`'] = hex_dict['ng`']
        hex_dict['五.'] = hex_dict['m`']
    else:
        hex_dict['五`'] = hex_dict['ng_m']
        hex_dict['五.'] = hex_dict['ng_m']

    return hex_dict
hex_dict = get_hex_dict("mapping.txt", ng_tilde=True)

def replace_r(syllable):
  # only replace r instances which are not in the first position
  return syllable[0] + syllable[1:].replace('r','w')
def factorize(syllable, replace_r=True):
  # literally the only exception which doesn't work, hardcode here
  if syllable == 'hng6': # 哼
    return 'h', 'ng', '6', ''
  # the number at the end of the string is the tone
  if syllable[-1].isdigit():
    tone = syllable[-1]
    syllable = syllable[:-1]
  else:
    tone = None
  # everything before the first vowel is the onset
  onset = ""
  i = 0
  while i < len(syllable) and (syllable[i] not in "aeiouy"):
    onset += syllable[i]
    i += 1
  if replace_r and len(onset) > 1 and onset[-1] == 'r':
    onset = onset[:-1] + 'w'

  remainder = syllable[i:]
  index = len(remainder)
  while index >= 0 and remainder[0:index] not in finals:
    index -= 1
    if remainder[0:index] in finals:
      break

  final = remainder[0:index]
  suffix = remainder[index:]
  is_syllabic = onset in {'m', 'ng'} and final == '' and suffix == ''
  return onset, final, suffix, tone, is_syllabic

def assemble(jping_tup, mode='font'):
  assert mode in ['web','font']
  onset, final, suffix, tone, is_syllabic = jping_tup
  if is_syllabic:
    thing = onset + "`" + tones[tone]
    if mode == 'web':
      return syllabics[onset] + tones[tone] + ("·" if tone in {"", None} else "")
    elif mode == 'font':
      return hex_dict[thing]
  else:
    has_zero = (onset == '' and final != '') or (onset != '' and final == '')
    thing = (onsets[onset] if onset in onsets else "".join(onsets[c] for c in onset)) \
          + finals[final] + ("`" if has_zero else "") + tones[tone]
    suffix_thing = "".join(onsets[c] for c in suffix) + \
      ("`" if len(suffix) == 1 else "")

    if mode == 'web':
      return thing + ("·" if tone in {"", None} else "") \
        + (suffix_thing + "·" if suffix != "" else "")
    elif mode == 'font':
      return hex_dict[thing] + (hex_dict[suffix_thing] if suffix != "" else "")

def transliterate(input, mode='font', orthography='honzi_jcz', use_repeat_char=True,
                  initial_r_block="r", v_block="v", tone_config='horizontal', use_schwa_char=False):
  assert mode in {'font', 'web'}
  assert orthography in {'jcz_only', 'honzi_jcz'}
  assert initial_r_block in {'r', 'wl', 'w'}
  assert v_block in {'v','f'}
  # use_schwa_char
  assert tone_config in {'horizontal','vertical'}

  # address component customizations
  # initial_r_block
  if initial_r_block == 'r':
    onsets['r'] = 'ㄖ'
  elif initial_r_block == 'wl':
    onsets['r'] = '禾力'
  elif initial_r_block == 'w':
    onsets['r'] = '禾'
  # v_block
  onsets['v'] = '圭' if v_block == 'v' else '夫'
  # use_schwa_char
  finals['a'] = '亇' if use_schwa_char else '乍'
  # tone_config
  tones['1'] = '¯' if tone_config == 'horizontal' else '\''
  tones['4'] = '⁼' if tone_config == 'horizontal' else '\"'

  # load CMU dictionary for using pronunciations
  con_cmu = sqlite3.connect('cmudict.db')
  cur_cmu = con_cmu.cursor()

  # load word segmentator
  wordsegment.load()

  outs, unparsed, word = [], set(), ""
  # ToJyutping has better pronunciation values compared to PyCantonese
  tj_parse = ToJyutping.get_jyutping_list(input)

  # parse words properly
  new_tj_parse, word, ptr = [], "", 0
  # A-Z and a-z only
  is_alphabetic = lambda x: x.isascii() and x.isalpha()
  is_alphanum = lambda x: x.isascii() and x.isalnum()
  while ptr < len(tj_parse):
    glyph, jping = tj_parse[ptr]
    if not is_alphabetic(glyph): # note sinoglyphs are alphabetic in unicode
      if glyph != " ":
        new_tj_parse.append(tj_parse[ptr])
      ptr += 1
    else:
      word = ""
      while is_alphabetic(glyph) and jping is None and ptr < len(tj_parse):
        glyph, jping = tj_parse[ptr]
        if is_alphabetic(glyph) and jping is None:
          word += glyph
          ptr += 1
      if word != " ":
        new_tj_parse.append((word, None))

  # perform the conversion to Honzi-Jyutping mix
  for i, pair in enumerate(new_tj_parse):
    glyphs, jpings = pair
    if jpings is not None:
      jping_arr = pc.parse_jyutping(jpings.replace(" ",""))
      for j, glyph in enumerate(glyphs):
        if orthography == 'jcz_only':
          outs.extend(jpings.split(" "))
        elif orthography == 'honzi_jcz':
          outs.append(str(jping_arr[j]) if glyph in mouth_list else glyph)
    elif glyphs in puncs or glyphs.isdigit():
      outs.append(glyphs)
    else:
      # attempt word segmentation to guesstimate pronuncation...
      words = wordsegment.segment(glyphs)
      # then attempt to convert the words into jyutping
      temp = []
      failed = False
      for word in words:
        parsed = word_to_jyutping(word, cur_cmu=cur_cmu)
        if parsed is not None:
          temp.extend(parsed)
        else:
          print("Warning: "+word+" from "+glyphs+" is not converted into Jyutping")
          failed = True
          break
      if failed:
        # fallback is to append original word and to not convert it into Jyutping
        # e.g. because it is a company name
        outs.append(glyphs)
        # keep track to make sure no attempts are made in converting it into Jyutping
        unparsed.add(glyphs)
      else:
        # jyutping successfully obtained
        outs.extend(temp)



  # convert Honzi-Jyutping to target orthography (JCZ-only or Honzi-JCZ)
  outs = [assemble(factorize(out), mode=mode) if is_alphanum(out) and len(out) > 1 and out not in unparsed else out for out in outs]

  # refine using repeat characters
  if use_repeat_char:
    if len(outs) > 1:
      new_outs = [outs[0]]
      i = 1
      while i < len(outs):
        if outs[i] == outs[i-1] and not (is_alphanum(outs[i])):
          new_outs.append("々")
        else:
          new_outs.append(outs[i])
        i += 1
      outs = new_outs

  # close CMU dictionary
  con_cmu.close()

  return "".join(outs)







import ToJyutping
import pycantonese as pc

## TODO: add option to use 改革漢字, e.g. for 哋
## TODO: add option for further cantonification of English pronunciations

puncs = '，！？：；（）［］【】。「」、‧《》〈〉'
# define all of the components
onsets = {'b': '比', 'p': '并', 'm': '文', 'f': '夫', 'd': '大', 't': '天',
          'n': '乃', 'l': '力', 'z': '止', 'c': '此', 's': '厶', 'j': '央',
          'g': '丩', 'k': '臼', 'h': '亾', 'ng': '爻', 'gw': '古', 'kw': '夸',
          'w': '禾', None: '', '': ''}
finals = {'aa':'乍', 'aai':'介', 'aau':'丂', 'aam':'彡', 'aan':'万',
          'aang':'生', 'aap':'甲', 'aat':'压', 'aak':'百', 'ai':'兮', 'au':'久',
          'am':'今', 'an':'云', 'ang':'亙', 'ap':'十', 'at':'乜', 'ak':'仄',
          'e':'旡', 'ei':'丌', 'eu':'了', 'em':'壬', 'en':'円', 'eng':'正',
          'ep':'夾', 'et':'叐', 'ek':'尺', 'i':'子', 'iu':'么', 'im':'欠',
          'in':'千', 'ing':'丁', 'ip':'頁', 'it':'必', 'ik':'夕', 'o':'个',
          'oi':'丐', 'ou':'冇', 'on':'干', 'ong':'王', 'ot':'匃', 'ok':'乇',
          'u':'乎', 'ui':'会', 'un':'本', 'ung':'工', 'ut':'末', 'uk':'玉',
          'oe':'居', 'oeng':'丈', 'oek':'勺', 'eoi':'句', 'eon':'卂', 'eot':'𥘅',
          'yu':'仒', 'yun':'元', 'yut':'乙', 'ng': '爻', None: '', '': ''}
tones = {'2': '´', '3': '`', '5': '˝', '6': 'ﾞ', None: '', '':''}
syllabics = {'ng': '五`', 'm': '五.'}

def get_hex_dict(file_loc, ng_tilde=False):
    # Note: "tilde" is supposed to mean tick here
    hex_dict = {'々': '々'}
    with open(file_loc) as file:
        for line in file.read().splitlines():
            hex_str, chars = line.split(" ")
            chars = chars.replace("oe","居")
            hex_dict[chars] = chr(int(hex_str, 16))
    if ng_tilde:
        hex_dict['五`'] = hex_dict['ng`']
        hex_dict['五.'] = hex_dict['m`']
    else:
        hex_dict['五`'] = hex_dict['ng_m']
        hex_dict['五.'] = hex_dict['ng_m']

    return hex_dict
hex_dict = get_hex_dict("mapping.txt", ng_tilde=True)

def replace_r(syllable):
  # only replace r instances which are not in the first position
  return syllable[0] + syllable[1:].replace('r','w')
def factorize(syllable, replace_r=True):
  # literally the only exception which doesn't work, hardcode here
  if syllable == 'hng6': # 哼
    return 'h', 'ng', '6', ''
  # the number at the end of the string is the tone
  if syllable[-1].isdigit():
    tone = syllable[-1]
    syllable = syllable[:-1]
  else:
    tone = None
  # everything before the first vowel is the onset
  onset = ""
  i = 0
  while i < len(syllable) and (syllable[i] not in "aeiouy"):
    onset += syllable[i]
    i += 1
  if replace_r and len(onset) > 1 and onset[-1] == 'r':
    onset = onset[:-1] + 'w'

  remainder = syllable[i:]
  index = len(remainder)
  while index >= 0 and remainder[0:index] not in finals:
    index -= 1
    if remainder[0:index] in finals:
      break

  final = remainder[0:index]
  suffix = remainder[index:]
  is_syllabic = onset in {'m', 'ng'} and final == '' and suffix == ''
  return onset, final, suffix, tone, is_syllabic

def assemble(jping_tup, mode='font'):
  assert mode in ['web','font']
  onset, final, suffix, tone, is_syllabic = jping_tup
  if is_syllabic:
    thing = onset + "`" + tones[tone]
    if mode == 'web':
      return syllabics[onset] + tones[tone] + ("·" if tone in {"", None} else "")
    elif mode == 'font':
      return hex_dict[thing]
  else:
    has_zero = (onset == '' and final != '') or (onset != '' and final == '')
    thing = (onsets[onset] if onset in onsets else "".join(onsets[c] for c in onset)) \
          + finals[final] + ("`" if has_zero else "") + tones[tone]
    suffix_thing = "".join(onsets[c] for c in suffix) + \
      ("`" if len(suffix) == 1 else "")

    if mode == 'web':
      return thing + ("·" if tone in {"", None} else "") \
        + (suffix_thing + "·" if suffix != "" else "")
    elif mode == 'font':
      return hex_dict[thing] + (hex_dict[suffix_thing] if suffix != "" else "")

def transliterate(input, mode='font', orthography='honzi_jcz', use_repeat_char=True,
                  initial_r_block="r", v_block="v", tone_config='horizontal', use_schwa_char=False):
  assert mode in {'font', 'web'}
  assert orthography in {'jcz_only', 'honzi_jcz'}
  assert initial_r_block in {'r', 'wl', 'w'}
  assert v_block in {'v','f'}
  # use_schwa_char
  assert tone_config in {'horizontal','vertical'}

  # address component customizations
  # initial_r_block
  if initial_r_block == 'r':
    onsets['r'] = 'ㄖ'
  elif initial_r_block == 'wl':
    onsets['r'] = '禾力'
  elif initial_r_block == 'w':
    onsets['r'] = '禾'
  # v_block
  onsets['v'] = '圭' if v_block == 'v' else '夫'
  # use_schwa_char
  finals['a'] = '亇' if use_schwa_char else '乍'
  # tone_config
  tones['1'] = '¯' if tone_config == 'horizontal' else '\''
  tones['4'] = '⁼' if tone_config == 'horizontal' else '\"'

  # load CMU dictionary for using pronunciations
  con_cmu = sqlite3.connect('cmudict.db')
  cur_cmu = con_cmu.cursor()

  # load word segmentator
  wordsegment.load()

  outs, unparsed, word = [], set(), ""
  # ToJyutping has better pronunciation values compared to PyCantonese
  tj_parse = ToJyutping.get_jyutping_list(input)

  # parse words properly
  new_tj_parse, word, ptr = [], "", 0
  # A-Z and a-z only
  is_alphabetic = lambda x: x.isascii() and x.isalpha()
  is_alphanum = lambda x: x.isascii() and x.isalnum()
  while ptr < len(tj_parse):
    glyph, jping = tj_parse[ptr]
    if not is_alphabetic(glyph): # note sinoglyphs are alphabetic in unicode
      if glyph != " ":
        new_tj_parse.append(tj_parse[ptr])
      ptr += 1
    else:
      word = ""
      while is_alphabetic(glyph) and jping is None and ptr < len(tj_parse):
        glyph, jping = tj_parse[ptr]
        if is_alphabetic(glyph) and jping is None:
          word += glyph
          ptr += 1
      if word != " ":
        new_tj_parse.append((word, None))

  # perform the conversion to Honzi-Jyutping mix
  for i, pair in enumerate(new_tj_parse):
    glyphs, jpings = pair
    if jpings is not None:
      jping_arr = pc.parse_jyutping(jpings.replace(" ",""))
      for j, glyph in enumerate(glyphs):
        if orthography == 'jcz_only':
          outs.extend(jpings.split(" "))
        elif orthography == 'honzi_jcz':
          outs.append(str(jping_arr[j]) if glyph in mouth_list else glyph)
    elif glyphs in puncs or glyphs.isdigit():
      outs.append(glyphs)
    else:
      # attempt word segmentation to guesstimate pronuncation...
      words = wordsegment.segment(glyphs)
      # then attempt to convert the words into jyutping
      temp = []
      failed = False
      for word in words:
        parsed = word_to_jyutping(word, cur_cmu=cur_cmu)
        if parsed is not None:
          temp.extend(parsed)
        else:
          print("Warning: "+word+" from "+glyphs+" is not converted into Jyutping")
          failed = True
          break
      if failed:
        # fallback is to append original word and to not convert it into Jyutping
        # e.g. because it is a company name
        outs.append(glyphs)
        # keep track to make sure no attempts are made in converting it into Jyutping
        unparsed.add(glyphs)
      else:
        # jyutping successfully obtained
        outs.extend(temp)



  # convert Honzi-Jyutping to target orthography (JCZ-only or Honzi-JCZ)
  outs = [assemble(factorize(out), mode=mode) if is_alphanum(out) and len(out) > 1 and out not in unparsed else out for out in outs]

  # refine using repeat characters
  if use_repeat_char:
    if len(outs) > 1:
      new_outs = [outs[0]]
      i = 1
      while i < len(outs):
        if outs[i] == outs[i-1] and not (is_alphanum(outs[i])):
          new_outs.append("々")
        else:
          new_outs.append(outs[i])
        i += 1
      outs = new_outs

  # close CMU dictionary
  con_cmu.close()

  return "".join(outs)

def file_transliterator(file, mode='font', orthography='honzi_jcz', use_repeat_char=True,
                  initial_r_block="r", v_block="v", tone_config='horizontal', use_schwa_char=False):
    with open(args.file, 'r') as f:
        return transliterate(f.read(), mode, orthography, use_repeat_char,
                          initial_r_block, v_block, tone_config, use_schwa_char)

    return "Error: couldn't read " + file

def pipe_transliterator(input, file=None, mode='font', orthography='honzi_jcz', use_repeat_char=True,
                  initial_r_block="r", v_block="v", tone_config='horizontal', use_schwa_char=False):
    return transliterate(input, mode, orthography, use_repeat_char,
                      initial_r_block, v_block, tone_config, use_schwa_char)

## code for running command
from argparse import ArgumentParser

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("-m", "--mode", dest="mode",
                        help="use font or web-style characters", metavar="MODE", default='font')
    parser.add_argument("-s", "--style", dest="orthography",
                        help="use jcz-only (jcz_only) or sinoglyph-jcz (honzi_jcz) writing style", metavar="STYLE", default='honzi_jcz')
    parser.add_argument("-r","--r_block", dest="initial_r_block",
                        help="whether to use r, wl or w for representing the onset 'r'",
                        metavar="R", default='r')
    parser.add_argument("-v","--v_block", dest="v_block",
                        help="whether to use v or f for representing the onset 'v'",
                        metavar="V", default='v')
    parser.add_argument("-t","--tone_config", dest="tone_config",
                        help="whether to use vertical or horizontal ticks for tones 1 and 4",
                        metavar="DIRECTION", default='horizontal')
    parser.add_argument("--use_repeat_char", dest="use_repeat_char",
                        help="whether to use the repeat glyph 々", metavar='BOOL', type=bool, default=True)
    parser.add_argument("--use_schwa_char", dest="use_schwa_char",
                        help="whether to use 亇 for the final 'a' instead of 乍", metavar='BOOL', type=bool, default=False)


    args = parser.parse_args()
    if not sys.stdin.isatty():
        print(pipe_transliterator(sys.stdin.read(), **vars(args)))
    else:
        title = "Interactive Jyutcitzi Interpreter"
        print(len(title)*"-")
        print(title)
        print(len(title)*"-")
        howto = "Howto: Input some text, and the JCZ transliterator will transliterate into the user-specified writing orthography."
        print(howto)
        print()
        while True:
            t = transliterate(input('Please enter your text (Quit with CTRL + C (*nix) or CTRL + Z (Windows)):\n'), **vars(args))
            if len(t) > 0:
                print('Output:')
                print(10*'-')
                print(t)
                print(10*'-')
            else:
                print('JCZ transliterator was unable to transliterate your text into JCZ.')
