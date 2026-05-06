import numpy as np
from .Cargo import Cargo
class Config:
    #   货物数据:编号, 类型, 长, 宽, 高, 重量, 数量
    CARGO_DATA = [
        ('G1', '标准件', 60, 40, 30, 12, 80),
        ('G2', '标准件', 50, 35, 25, 8, 100),
        ('G3', '易碎件', 70, 50, 40, 15, 30),
        ('G4', '定向件', 80, 60, 50, 25, 40),
        ('G5', '定向件', 40, 40, 60, 18, 50),
    ]

def expand_cargo_data():
    """将CARGO_DATA按数量展开为Cargo对象列表"""
    cargo_list = []
    for id_, type_, l, w, h, weight, qty in Config.CARGO_DATA:
        for i in range(qty):
            # 生成唯一ID
            unique_id = f"{id_}_{i+1}"
            cargo = Cargo(unique_id, type_, l, w, h, weight, 1)
            cargo_list.append(cargo)
    return cargo_list

