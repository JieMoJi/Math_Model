import numpy as np

class Cargo:
    def __init__(self, id_, type_, l, w, h, weight, qty):
        # 基础属性
        self.id = id_
        self.type = type_
        self.l = l
        self.w = w
        self.h = h
        self.weight = weight
        self.qty = qty

        # 计算体积和密度
        self.volume = l * w * h
        self.density = weight / self.volume

        # 约束标签
        self.is_fragile = (type_ == '易碎件')
        self.can_stack = (type_ != '易碎件')

        # 姿态矩阵
        self.rotations = self._get_rotations()

    def _get_rotations(self):
        l, w, h = self.l, self.w, self.h
        if self.type == '标准件':
            return [
                (l, w, h), (l, h, w),
                (w, l, h), (w, h, l),
                (h, l, w), (h, w, l)
            ]
        elif self.type == '定向件':
            return [(l, w, h), (w, l, h)]
        elif self.type == '易碎件':
            return [(l, w, h), (w, l, h)]
        else:
            return [(l, w, h)]