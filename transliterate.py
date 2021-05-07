import sys, sqlite3, re, warnings
import ToJyutping
import pycantonese as pc
import wordsegment
from words_to_jyutping import word_to_jyutping
from mouth_radicals import mouth_list

# ONLY works for phrases from jyut6ping3.lettered.dict.yaml
def extract_components(input, orthography='honzi_jcz'):
  assert orthography in {'honzi_jcz','jcz_only'}
  is_alphabetic = lambda x: x.isascii() and x.isalpha()
  jpings_list = pc.characters_to_jyutping(input)
  assert len(jpings_list) == 1
  _ , jpings = jpings_list[0]
  x = pc.parse_jyutping(jpings)
  if orthography == 'jcz_only':
    return [str(y) for y in x]

  targets = [pc.characters_to_jyutping(glyph)[0] for glyph in input \
              if not is_alphabetic(glyph) and glyph != "-"]
  idx = 0
  tgt_idx = 0
  outs = []
  while idx < len(x):
    elem = x[idx]
    if tgt_idx >= len(targets):
      outs.extend([str(y) for y in x[idx:]])
      return outs
    if str(elem)[:-1] == targets[tgt_idx][1][:-1]:
      if targets[tgt_idx][0] in mouth_list:
        outs.append(str(elem))
      else:
        outs.append(targets[tgt_idx][0])
      tgt_idx += 1
    else:
      outs.append(str(elem))
    idx += 1
  return outs


## TODO: add option to use 改革漢字, e.g. for 哋
## TODO: add option for further cantonification of English pronunciations

puncs = '！？｡。＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏.'
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
jping_rgx = re.compile('^(([bBpPmMfFdDtTnNlLzZcCsSjJgGkKhHwrRvV]|ng|gw|kw|)((aa(i|u|m|ng|n|p|t|k|))|(a(a|i|u|m|ng|n|p|t|k|))|(oe(ng|k|))|(eo(i|n|t))|(e(i|u|m|ng|n|p|t|k|))|(i(u|m|ng|n|p|t|k|))|(o(i|u|ng|n|t|k|))|(yu(n|t|))|(u(i|ng|n|t|k|))|z)|(m|ng|er))([1-6]?)$')


def words_to_jyutping(glyphs, cur_cmu, outs, unparsed, prev_was_eng_word):
  if prev_was_eng_word:
    # add space if previous and current input are english words
    outs.append(" ")
    prev_was_eng_word = False

  hngs = {'hng','hng1','hng2','hng3','hng4','hng5','hng6'}
  try:
    assemble(factorize(glyphs))
    is_jyutping = True
  except:
    is_jyutping = False

  if is_jyutping or (len(glyphs) == 1 and glyphs.isupper()):# re.match(jping_rgx, glyphs) or glyphs in hngs:
    # glyphs is jyutping, no need to process
    outs.append(glyphs)
  else:
    fragments = list(filter(None, re.split('(\d+)', glyphs)))
    for frag in fragments:
      # attempt word segmentation to guesstimate pronuncation...
      words = wordsegment.segment(frag)
      # then attempt to convert the words into jyutping
      temp = []
      failed = False
      for word in words:
        parsed = word_to_jyutping(word, cur_cmu=cur_cmu)
        if parsed is not None:
          temp.extend(parsed)
        else:
          warnings.warn("Warning: "+word+" from "+frag+" is not converted into Jyutping")
          failed = True
          break
      if failed:
        # fallback is to append original word and to not convert it into Jyutping
        # e.g. because it is a company name
        outs.append(frag)
        # keep track to make sure no attempts are made in converting it into Jyutping
        unparsed.add(frag)
        prev_was_eng_word = False
      else:
        # jyutping successfully obtained
        outs.extend(temp)
        prev_was_eng_word = True
  return outs, unparsed, prev_was_eng_word

def pycantonese_converter(input, cur_cmu, orthography='honzi_jcz', sep_eng_words=True):
  assert orthography in {'honzi_jcz','jcz_only'}
  frags = re.split(r'(\s+)', input) # preserve whitespace except space character
  frags = list(filter(lambda x: x not in {'', ' '}, frags))
  outs, unparsed = [], set()
  prev_was_eng_word = False # used for adding space between words
  for frag in frags:
    if frag.isspace() and (frag != ' ' and sep_eng_words):
      outs.append(frag)
      prev_was_eng_word = False
      continue
    for glyphs, jpings in pc.characters_to_jyutping(frag):
      if jpings is not None:
        jping_arr = pc.parse_jyutping(jpings)
        if re.search('[a-zA-Z]', glyphs):
          # this is a dictionary entry with both honzi and latin characters
          outs.extend(extract_components(glyphs, orthography=orthography))
        else:
          if orthography == 'jcz_only':
            outs.extend([str(x) for x in jping_arr])
          else:
            for i, glyph in enumerate(glyphs):
              outs.append(str(jping_arr[i]) if glyph in mouth_list else glyph)
        prev_was_eng_word = False
      elif len(glyphs) == 1 and not is_alphanum(glyphs): #glyphs in puncs or glyphs.isdigit():
        outs.append(glyphs)
        prev_was_eng_word = False
      else:
        outs, unparsed, prev_was_eng_word = words_to_jyutping(glyphs, cur_cmu,
                    outs, unparsed, prev_was_eng_word and sep_eng_words)
  return outs, unparsed

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
  if syllable[0:3] == 'hng': # 哼[1-6]
    return 'h', 'ng', '', syllable[3:], False
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
    if onset == '' and final != '' and len(suffix) == 1 and not is_syllabic:
      # deal with stuff like ('', 'e', 's', None, False), not 'esh'
      thing = finals[final] + onsets[suffix] + tones[tone]
      suffix_thing = ""
    else:
      has_zero = (onset == '' and final != '') \
                  or (onset != '' and final == '' and len(onset) == 1)
      thing = (onsets[onset] if onset in onsets else "".join(onsets[c] for c in onset)) \
            + finals[final] + ("`" if has_zero else "") + tones[tone]

      suffix_thing = "".join(onsets[c] for c in suffix) + \
        ("`" if len(suffix) == 1 else "")

    if mode == 'web':
      return thing + ("·" if tone in {"", None} else "") \
        + (suffix_thing + "·" if suffix != "" else "")
    elif mode == 'font':
      return hex_dict[thing] + (hex_dict[suffix_thing] if suffix_thing != "" else "")

is_alphabetic = lambda x: x.isascii() and x.isalpha()
is_alphanum = lambda x: x.isascii() and x.isalnum()
is_loweralphanum = lambda x: x.isascii() and x.isalnum() and (x.islower() or (x.isdigit() and len(x) == 1))
def tojyutping_converter(input, cur_cmu, orthography='honzi_jcz', sep_eng_words=True):
  # input: original input from transliterate, cur_cmu
  # output: array of syllables/glyphs (outs)

  outs, unparsed, word = [], set(), ""

  # ToJyutping has better pronunciation values compared to PyCantonese
  tj_parse = ToJyutping.get_jyutping_list(input)

  # parse words properly
  # i.e. convert [('做', 'zou6'), ('g', None), ('y', None), ('m', None)]
  # to [('做', 'zou6'), ('gym', None)]
  new_tj_parse, word, ptr = [], "", 0
  # A-Z and a-z and 0-9 only
  while ptr < len(tj_parse):
    glyph, jping = tj_parse[ptr]
    # print(glyph, jping)
    if not is_loweralphanum(glyph): # note sinoglyphs are alphabetic in unicode
      if glyph != " ":
        new_tj_parse.append(tj_parse[ptr])
      ptr += 1
    else:
      word = ""
      while is_loweralphanum(glyph) and jping is None and ptr < len(tj_parse):
        # print("word =", word)
        glyph, jping = tj_parse[ptr]
        if is_loweralphanum(glyph) and jping is None:
          word += glyph
          ptr += 1
        else:
          break
      if word != " ":
        new_tj_parse.append((word, None))

  prev_was_eng_word = False # used for adding space between words

  # perform the conversion to Honzi-Jyutping mix
  # i.e. convert [('做', 'zou6'), ('gym', None)] to ['做','zim1']
  for i, pair in enumerate(new_tj_parse):
    glyphs, jpings = pair
    if jpings is not None:
      jping_arr = pc.parse_jyutping(jpings.replace(" ",""))
      for j, glyph in enumerate(glyphs):
        if orthography == 'jcz_only':
          outs.extend(jpings.split(" "))
        elif orthography == 'honzi_jcz':
          outs.append(str(jping_arr[j]) if glyph in mouth_list else glyph)
      prev_was_eng_word = False
    elif len(glyphs) == 1 and not is_alphanum(glyphs): #glyphs in puncs or glyphs.isdigit():
      outs.append(glyphs)
      prev_was_eng_word = False
    else:
      outs, unparsed, prev_was_eng_word = words_to_jyutping(glyphs, cur_cmu,
                outs, unparsed, prev_was_eng_word and sep_eng_words)
  return outs, unparsed

def transliterate(input, mode='font', orthography='honzi_jcz', use_repeat_char=True,
                  initial_r_block="r", v_block="v", tone_config='horizontal',
                  use_schwa_char=False, algorithm="PyCantonese", sep_eng_words=True):
  assert mode in {'font', 'web'}
  assert orthography in {'jcz_only', 'honzi_jcz'}
  assert initial_r_block in {'r', 'wl', 'w'}
  assert v_block in {'v','f'}
  # use_schwa_char
  assert tone_config in {'horizontal','vertical'}
  assert algorithm in {'PyCantonese','ToJyutping'}

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

  # convert input string into a list of sinoglyph/jyutping syllables
  converter = tojyutping_converter if algorithm == "ToJyutping" \
                                  else pycantonese_converter
  outs, unparsed = converter(input, cur_cmu, orthography=orthography,
                             sep_eng_words=sep_eng_words)

  # convert (Honzi-)Jyutping to target mode (web or font)
  outs_neo = []
  for out in outs:
    if is_alphanum(out) and out.islower() and out not in unparsed:
      try:
        outs_neo.append(assemble(factorize(out), mode=mode))
      except:
        outs_neo.append(out)
    else:
      outs_neo.append(out)

  outs = outs_neo

  # refine using repeat characters
  if use_repeat_char:
    if len(outs) > 1:
      new_outs = [outs[0]]
      i = 1
      while i < len(outs):
        if outs[i] == outs[i-1] and not (is_alphanum(outs[i])) and not outs[i] in puncs:
          new_outs.append("々")
        else:
          new_outs.append(outs[i])
        i += 1
      outs = new_outs

  # close CMU dictionary
  con_cmu.close()

  return "".join(outs).replace('\u2028','\n')

# (input, mode='font', orthography='honzi_jcz', use_repeat_char=True,
                  # initial_r_block="r", v_block="v", tone_config='horizontal',
                  # use_schwa_char=False, algorithm="PyCantonese", sep_eng_words=True)

def file_transliterator(file, mode='font', orthography='honzi_jcz', use_repeat_char=True,
                  initial_r_block="r", v_block="v", tone_config='horizontal',
                  use_schwa_char=False, algorithm="PyCantonese", sep_eng_words=True):
    with open(args.file, 'r') as f:
        return transliterate(f.read(), mode, orthography, use_repeat_char,
                          initial_r_block, v_block, tone_config, use_schwa_char,
                          algorithm, sep_eng_words)

    return "Error: couldn't read " + file

def pipe_transliterator(input, file=None, mode='font', orthography='honzi_jcz',
                  use_repeat_char=True, initial_r_block="r", v_block="v",
                  tone_config='horizontal', use_schwa_char=False,
                  algorithm="PyCantonese", sep_eng_words=True):
    return transliterate(input, mode, orthography, use_repeat_char,
                      initial_r_block, v_block, tone_config, use_schwa_char,
                      algorithm, sep_eng_words)

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
    parser.add_argument("-a","--alg", dest="algorithm",
                        help="algorithm for obtaining Jyutping romanizations: PyCantonese or ToJyutping",
                        metavar="ALGORITHM", default='PyCantonese')

    args = parser.parse_args()
    if not sys.stdin.isatty():
        print(pipe_transliterator(sys.stdin.read(), **vars(args)))
    else:
        title = "Interactive Jyutcitzi Transliterator"
        print(len(title)*"-")
        print(title)
        print(len(title)*"-")
        howto = "Howto: Input some text, and the JCZ transliterator will transliterate into the user-specified Cantonese orthography."
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
