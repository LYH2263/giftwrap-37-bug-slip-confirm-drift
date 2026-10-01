"""核销校验：确认前判定纸条是否可核销。"""
from fastapi import HTTPException


def require_open(ticket: dict) -> None:
    if ticket["status"] != "open":
        raise HTTPException(409, f"纸条 {ticket['code']} 已核销或失效，不可重复确认")


def require_face_unchanged(ticket: dict, current_box: dict, current_overlap: float) -> None:
    if current_box is None:
        raise HTTPException(409, "礼盒已不存在，票面无法核对")

    for dim, label in (("length", "长"), ("width", "宽"), ("height", "高")):
        if float(current_box[dim]) != float(ticket[dim]):
            raise HTTPException(
                409,
                f"盒边{label}已由票面 {ticket[dim]} 变为 {float(current_box[dim])}，纸条作废",
            )
    # 折边系数同属票面：漂移即作废
    if float(current_overlap) != float(ticket["overlap"]):
        raise HTTPException(
            409,
            f"折边系数已由票面 {ticket['overlap']} 变为 {float(current_overlap)}，纸条作废",
        )
