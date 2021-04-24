# jyutcitzi-transliterate

A simple Python3 tool for the transliteration of the existing Sinoglyph-Latin script used in Hong Kong Cantonese into either a Jyutcitzi-only or Honzi-Jyutcitzi mixed script.

## Example
```
$ cat sample.txt
喂，我哋唔係啱啱已經喺嗰度好咧啡噉噏咗你嗰啲咁𠵇𠺫嘅嘢㗎喇咩？嗱，你唔好咁忟憎先。喂你咪諗住玩我呀，我已經噒熟咗份嘢㗎啦。我哋淨話個presentation已經cover嗮阿Tim prepare嗰份document入面啲bullet point㗎嘞，你之前想幫手proofread份嘢就早響吖嘛。重有呀，你鬧乜Q唧，我噚日都係啱先喺Budapest飛返嚟咋嘛，使唔使咁火滾呀？唉算喇，我哋不如都係下個禮拜再開會傾過啦係咪先，我而家要趕住去健身中心做gym keep fit，係噉先啦掰掰。
$ python transliterate.py sample.txt --mode web
禾兮`，我大丌ﾞ五.⁼係爻彡¯々已經亾兮´丩个´度好力旡`夫旡¯丩今´噏止个´你丩个´大子¯丩今`臼了⁼力了¯丩旡´央旡˝丩乍`力乍`文旡¯？乃乍⁼，你五.⁼好丩今`忟憎先。禾兮`你文兮ﾞ諗住玩我乍`⁼，我已經力卂¯熟止个´份央旡˝丩乍`力乍¯。我大丌ﾞ淨話個并禾旡·厶`·厶云·天丌·厶亾云·已經臼乍·夫乍·厶介`阿天欠·并禾子·并旡·乍`·丩个´份大百·臼央今·文円·入面大子¯比乎·力乜·并丐·乃`·丩乍`力乍`，你之前想幫手并禾乎·夫`·夫禾必·份央旡˝就早響乍`¯文乍`。重有乍`⁼，你鬧乜臼么·止夕¯，我此今⁼日都係爻彡¯先亾兮´比乎·大十·并旡·厶天·飛返力兮⁼止乍¯文乍`，使五.⁼使丩今`火滾乍`⁼？介`¯算力乍`，我大丌ﾞ不如都係下個禮拜再開會傾過力乍¯係文兮ﾞ先，我而家要趕住去健身中心做止央欠·臼頁·夫必·，係丩今´先力乍¯掰々。
$ python transliterate.py sample.txt > out.txt
```
![alt text](https://github.com/jyutcitzi/jyutcitzi-transliterate/blob/6416ded789db13e416cde9990221d6a098cf7ceb/images/out.png "out.txt")

## Installation
```
pip install ToJyutping
pip install pycantonese
pip install wordsegment
```
In order to render the Jyutcitzi glyphs when using the font mode, install the fonts at https://github.com/jyutcitzi/jyutcitzi-fonts.

## Usage
```
usage: transliterate.py [-h] [-m MODE] [-s STYLE] [-r R] [-v V] [-t DIRECTION]
                        [--use_repeat_char BOOL] [--use_schwa_char BOOL]
                        FILE

positional arguments:
  FILE                  read input text from FILE

optional arguments:
  -h, --help            show this help message and exit
  -m MODE, --mode MODE  use font or web-style characters
  -s STYLE, --style STYLE
                        use jcz-only (jcz_only) or sinoglyph-jcz (honzi_jcz)
                        writing style
  -r R, --r_block R     whether to use r, wl or w for representing the onset
                        'r'
  -v V, --v_block V     whether to use v or f for representing the onset 'v'
  -t DIRECTION, --tone_config DIRECTION
                        whether to use vertical or horizontal ticks for tones
                        1 and 4
  --use_repeat_char BOOL
                        whether to use the repeat glyph 々
  --use_schwa_char BOOL
                        whether to use 亇 for the final 'a' instead of 乍
```
