from datetime import date as D
from engine import Cand, plan

TODAY, REC = D(2026,11,5), D(2026,11,24)
A = dict(profile={"type":"general","round":6}, today=TODAY, rec_day=REC, cands=[
    Cand("job", D(2026,11,12), "OO제조 품질관리"), Cand("job", D(2026,11,19), "XX물류 사무"),
    Cand("training", D(2026,11,24), "직무전환 훈련"), Cand("work", D(2026,11,21), "단기 알바"),
    Cand("exam", D(2026,12,5), "자격시험")])
B_ok = dict(profile={"type":"repeat","round":5}, today=TODAY, rec_day=REC, cands=[
    Cand("job", D(2026,11,12), "공고1"), Cand("job", D(2026,11,19), "공고2"), Cand("lecture", D(2026,11,10), "취업특강")])
B_short = dict(profile={"type":"repeat","round":5}, today=TODAY, rec_day=REC, cands=[
    Cand("job", D(2026,11,12), "공고1"), Cand("lecture", D(2026,11,10), "취업특강")])
C = dict(profile={"type":"senior","round":3}, today=TODAY, rec_day=REC, cands=[Cand("lecture", D(2026,11,10), "취업특강")])
D_work = dict(profile={"type":"general","round":3}, today=TODAY, rec_day=REC, cands=[
    Cand("work", D(2026,11,21), "단기 알바"), Cand("job", D(2026,11,12), "공고1")])
MISMATCH = dict(profile={"type":"general","round":6}, today=TODAY, rec_day=REC, cands=[
    Cand("job", D(2026,11,12), "무관 직종 공고", matches_target=False), Cand("job", D(2026,11,19), "일치 공고")])
if __name__ == "__main__":
    r = plan(**A)
    for d, s in r["steps"]: print(d, s)
    for t, m in r["alerts"]: print("[경고]", t, "-", m)
    print("신청:", r["apply"], "| 충족:", r["ok"])
