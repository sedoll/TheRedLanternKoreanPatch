"""The Red Lantern 한글패치 빌드 스크립트.

원본(패치되지 않은) 게임 파일과 translation/ko.tsv, fonts/NotoSansKR-Game.ttf 로
patch/ 폴더의 결과물을 다시 만든다.

    pip install UnityPy
    python tools/build.py "D:/SteamLibrary/steamapps/common/The Red Lantern"

동작 방식
- StreamingAssets/Flume/TheRedLantern_v001-Built.twig (gzip + protobuf) 의
  영어(0)·일본어(5) 슬롯과 기본 텍스트를 한국어로 교체한다.
- managers_and_interfaces_assets_guimanager.bundle 의 동적 TMP 폰트(NotoSansJP)를
  한글 폰트로 바꾸고, 영어/일본어 LanguageFontMap 이 모두 이 폰트를 쓰도록 연결한다.
"""
import gzip
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TWIG_REL = 'TheRedLantern_sw_Data/StreamingAssets/Flume/TheRedLantern_v001-Built.twig'
BUNDLE_REL = 'TheRedLantern_sw_Data/StreamingAssets/aa/StandaloneWindows64/managers_and_interfaces_assets_guimanager.bundle'
SLOTS = (0, 5)  # 0 = English, 5 = Japanese

# ---------------------------------------------------------------- protobuf helpers
def varint(b, i):
    r = s = 0
    while True:
        c = b[i]; i += 1; r |= (c & 0x7f) << s; s += 7
        if c < 0x80:
            return r, i


def enc_varint(n):
    out = bytearray()
    while True:
        b = n & 0x7f; n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b); return bytes(out)


def fld_bytes(f, data):
    return enc_varint((f << 3) | 2) + enc_varint(len(data)) + data


def fld_varint(f, v):
    return enc_varint(f << 3) + enc_varint(v)


def raw_fields(b):
    i = 0
    while i < len(b):
        s = i; k, i = varint(b, i); f, t = k >> 3, k & 7
        if t == 0:
            v, i = varint(b, i)
        elif t == 2:
            l, i = varint(b, i); v = b[i:i + l]; i += l
        elif t == 5:
            v = b[i:i + 4]; i += 4
        elif t == 1:
            v = b[i:i + 8]; i += 8
        else:
            raise ValueError('wire type %d' % t)
        yield f, t, v, b[s:i]


def packed(b):
    i = 0; r = []
    while i < len(b):
        v, i = varint(b, i); r.append(v)
    return r

# ---------------------------------------------------------------- twig
def read_entries(twig):
    """yield (key, english_text) from decompressed twig."""
    for _, _, v, _ in raw_fields(twig):
        key = None; en = None; default = None
        for f2, _, v2, _ in raw_fields(v):
            if f2 == 1:
                key = v2.decode('utf8')
            elif f2 == 2:
                for f3, t3, v3, _ in raw_fields(v2):
                    if f3 == 5:
                        lid = 0; txt = None
                        for f4, _, v4, _ in raw_fields(v3):
                            if f4 == 1: lid = v4
                            elif f4 == 2: txt = v4.decode('utf8')
                        if lid == 0: en = txt
                    elif f3 == 6:
                        default = v3.decode('utf8')
        yield key, en if en is not None else (default or '')


SPLIT = re.compile(r'^(\s*(?:%\?|\?%|%)?\s*)(.*?)(\s*)$', re.S)


def make_ko_map(twig, table):
    out = {}; miss = 0
    for key, en in read_entries(twig):
        m = SPLIT.match(en)
        core = m.group(2)
        if core in table:
            out[key] = m.group(1) + table[core] + m.group(3)
        elif core.strip():
            miss += 1
    return out, miss


def loc_entry(lid, text):
    return fld_bytes(5, (fld_varint(1, lid) if lid else b'') + fld_bytes(2, text.encode('utf8')))


def rebuild_record(rec, ko):
    fields = list(raw_fields(rec)); out = bytearray(); wrote = False
    has3 = any(f == 3 for f, *_ in fields)
    for f, t, v, raw in fields:
        if f == 3 and t == 2:
            out += fld_bytes(3, b''.join(enc_varint(x) for x in sorted(set(packed(v)) | set(SLOTS)))); continue
        if f == 5 and t == 2:
            lid = 0
            for f2, _, v2, _ in raw_fields(v):
                if f2 == 1: lid = v2
            if lid in SLOTS: continue
        if f == 6 and t == 2:
            if not wrote:
                if not has3:
                    out += fld_bytes(3, b''.join(enc_varint(x) for x in SLOTS))
                for lid in SLOTS: out += loc_entry(lid, ko)
                wrote = True
            out += fld_bytes(6, ko.strip().encode('utf8')); continue
        out += raw
    if not wrote:
        for lid in SLOTS: out += loc_entry(lid, ko)
    return bytes(out)


def build_twig(src, dst, table):
    twig = gzip.decompress(open(src, 'rb').read())
    ko, miss = make_ko_map(twig, table)
    out = bytearray()
    for _, _, v, raw in raw_fields(twig):
        parts = list(raw_fields(v))
        key = next((v2.decode('utf8') for f2, _, v2, _ in parts if f2 == 1), None)
        if key in ko:
            nv = bytearray()
            for f2, _, v2, raw2 in parts:
                nv += fld_bytes(2, rebuild_record(v2, ko[key])) if f2 == 2 else raw2
            out += fld_bytes(1, bytes(nv))
        else:
            out += raw
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'wb').write(gzip.compress(bytes(out), compresslevel=9, mtime=0))
    print(f'twig: {len(ko)} entries translated, {miss} untranslated')

# ---------------------------------------------------------------- bundle
FONT = 3022442500999855162    # Font  NotoSansJP-Regular
ASSET = 3994462501187428527   # TMP_FontAsset NotoSansJP-Regular SDF (dynamic)
ATLAS = 2110308696405275859   # Texture2D atlas


def build_bundle(src, dst, fontpath):
    import UnityPy
    env = UnityPy.load(src)
    fd = open(fontpath, 'rb').read()
    for o in env.objects:
        if o.path_id == FONT:
            tt = o.read_typetree(); tt['m_FontData'] = fd; tt['m_FontNames'] = ['Noto Sans KR']; o.save_typetree(tt)
        elif o.path_id == ATLAS:
            tt = o.read_typetree(); tt['image data'] = bytes(len(tt['image data'])); o.save_typetree(tt)
        elif o.path_id == ASSET:
            tt = o.read_typetree(); W, H = tt['m_AtlasWidth'], tt['m_AtlasHeight']
            tt['m_GlyphTable'] = []; tt['m_CharacterTable'] = []; tt['m_UsedGlyphRects'] = []
            tt['m_FreeGlyphRects'] = [{'m_X': 0, 'm_Y': 0, 'm_Width': W - 1, 'm_Height': H - 1}]
            tt['m_IsMultiAtlasTexturesEnabled'] = 1
            tt['m_AtlasPopulationMode'] = 1
            tt['m_FaceInfo']['m_FamilyName'] = 'Noto Sans KR'
            tt['m_CreationSettings']['characterSequence'] = ''
            o.save_typetree(tt)
        elif o.type.name == 'MonoBehaviour':
            tt = o.read_typetree()
            if 'Localization' in tt and 'From' in tt and 'To' in tt:  # LanguageFontMap
                tt['To'] = {'m_FileID': 0, 'm_PathID': ASSET}; o.save_typetree(tt)
                print('font map ->', tt['m_Name'])
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'wb').write(env.file.save(packer='lz4'))
    print('bundle: saved')

# ---------------------------------------------------------------- main
def load_table(path):
    table = {}
    with open(path, encoding='utf8') as f:
        next(f)
        for ln in f:
            ln = ln.rstrip('\n')
            if not ln: continue
            _, en, ko = ln.split('\t', 2)
            table[en.replace('\\n', '\n')] = ko.replace('\\n', '\n')
    return table


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    game = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'patch')
    table = load_table(os.path.join(ROOT, 'translation', 'ko.tsv'))
    build_twig(os.path.join(game, TWIG_REL), os.path.join(out, TWIG_REL), table)
    build_bundle(os.path.join(game, BUNDLE_REL), os.path.join(out, BUNDLE_REL),
                 os.path.join(ROOT, 'fonts', 'NotoSansKR-Game.ttf'))


if __name__ == '__main__':
    main()
