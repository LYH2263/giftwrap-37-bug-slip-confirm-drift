"""估纸条业务模块：
- ticket：签发一次性估纸条并登记票面快照
- redeem：确认前核销校验（缺条/已核销/票面已变）
- paper_run：单事务内写用纸档一行并标记核销

bag_mode / double_wrap / print_label / ribbon_bow 仍是 0-1 占位，未接入。
"""
