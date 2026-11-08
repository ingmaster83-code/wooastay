#!/usr/bin/env python3
"""
process_data.py (우아숙박) - 행안부 LOCALDATA 숙박업 CSV(영업/정상)를 가공한다.
입력: data/raw/lodgings.csv   출력: _rawdata/st_{시도}.json, search_index.json
종류 분류: 등록 업태(관광호텔·휴양콘도미니엄업)가 우선, 그 다음 상호 키워드(펜션→게스트하우스→모텔→호텔), 나머지는 업태(여관업·여인숙업→여관·여인숙, 그 외→생활숙박).
객실 수 = 양실수(침대방)+한실수(온돌방). 신고 당시 값이라 실제와 다를 수 있다.
"""
import re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib_localdata import *  # noqa

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "raw"
CATMETA = {
    "모텔": ("motel", "🏩"), "호텔": ("hotel", "🏨"), "관광호텔": ("tourist-hotel", "🛎️"), "펜션·풀빌라": ("pension", "🏡"),
    "게스트하우스·호스텔": ("guesthouse", "🛏️"), "리조트·콘도": ("resort", "🏖️"), "여관·여인숙": ("inn", "🏮"), "생활숙박": ("residence", "🏢"),
}
RE_PENSION = re.compile(r"펜션|풀빌라|독채|글램핑|카라반|pension", re.I)
RE_GUEST = re.compile(r"게스트|호스텔|hostel|guest|도미토리|민박", re.I)
RE_MOTEL = re.compile(r"모텔|무인텔|motel", re.I)
RE_HOTEL = re.compile(r"호텔|hotel", re.I)
RE_RESORT = re.compile(r"리조트|콘도|resort|condo", re.I)
RE_INN = re.compile(r"여관|여인숙")


def classify(biz, name):
    if biz == "관광호텔":
        return "관광호텔"
    if biz == "휴양콘도미니엄업":
        return "리조트·콘도"
    if RE_PENSION.search(name):
        return "펜션·풀빌라"
    if RE_GUEST.search(name):
        return "게스트하우스·호스텔"
    if RE_MOTEL.search(name):
        return "모텔"
    if RE_HOTEL.search(name) or biz == "일반호텔":
        return "호텔"
    if RE_RESORT.search(name):
        return "리조트·콘도"
    if biz in ("여관업", "여인숙업") or RE_INN.search(name):
        return "여관·여인숙"
    return "생활숙박"


def main():
    tf = make_transformer()
    records = []
    for r in read_csv_rows(RAW / "lodgings.csv"):
        if clean(r.get("영업상태명")) != "영업/정상":
            continue
        name = clean(r.get("사업장명"))
        biz = clean(r.get("업태구분명"))
        cat = classify(biz, name)
        yang = int(num(r.get("양실수")))
        han = int(num(r.get("한실수")))
        if not (0 <= yang <= 3000):
            yang = 0
        if not (0 <= han <= 3000):
            han = 0
        rooms = yang + han
        area = num(r.get("소재지면적"))
        floors = int(num(r.get("건물지상층수")))
        if not (0 < floors <= 120):
            floors = 0
        lat, lng = to_wgs(tf, r.get("좌표정보(X)"), r.get("좌표정보(Y)"))
        extras, hrows = [], []
        if biz:
            extras.append({"l": "등록 업태", "v": biz})
        if rooms > 0:
            extras.append({"l": "객실 수", "v": f"{rooms}실"})
            hrows.append({"i": "🛏️", "t": f"객실 {rooms}실" + (f" (침대방 {yang} · 온돌방 {han})" if yang and han else "")})
        if area > 0:
            extras.append({"l": "시설 면적", "v": f"{area:,.0f}㎡"})
        if floors > 0:
            extras.append({"l": "건물 층수", "v": f"지상 {floors}층"})
        records.append(dict(name=name, cat=cat, road=r.get("도로명주소"), lot=r.get("지번주소"), tel=r.get("전화번호"),
                            permit=r.get("인허가일자"), upd=clean(r.get("최종수정시점"))[:10], lat=lat, lng=lng,
                            extras=extras, hrows=hrows, note=f"객실 {rooms}실" if rooms > 0 else "", subtype=biz,
                            rooms=rooms, yang=yang, han=han, floors=floors, area=round(area)))
    finalize(records, ROOT / "_rawdata", "st", ROOT, CATMETA)


if __name__ == "__main__":
    main()
