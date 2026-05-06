import numpy as np

class Truck:
    def __init__(self, truck_type):
        # 车型1和车型2的尺寸（单位：cm），已扣除3cm安全间隙
        if truck_type == 1:
            self.L, self.W, self.H = 420, 210, 217  # 原始高220，扣除3
            self.max_weight = 6000  # kg
            self.cost = 450
        else:  # truck_type == 2
            self.L, self.W, self.H = 680, 245, 247  # 原始高250，扣除3
            self.max_weight = 10000
            self.cost = 700

        # 状态记录
        self.loaded_items = []  # 已装货物列表，每个元素为 (cargo, position, rotation)
        self.used_volume = 0
        self.used_weight = 0
        self.ep_list = [(0, 0, 0)]  # 极点列表，初始只有原点

    def _ep_sort_key(self, ep):
        # 排序优先级：Z升序 -> Y升序 -> X升序
        return (ep[2], ep[1], ep[0])

    def _aabb_overlap(self, pos1, dim1, pos2, dim2):
        # 判断两个轴对齐长方体是否重叠
        x1_min, y1_min, z1_min = pos1
        x1_max = x1_min + dim1[0]
        y1_max = y1_min + dim1[1]
        z1_max = z1_min + dim1[2]

        x2_min, y2_min, z2_min = pos2
        x2_max = x2_min + dim2[0]
        y2_max = y2_min + dim2[1]
        z2_max = z2_min + dim2[2]

        # 在任一轴上分离则无重叠
        if x1_max <= x2_min or x2_max <= x1_min:
            return False
        if y1_max <= y2_min or y2_max <= y1_min:
            return False
        if z1_max <= z2_min or z2_max <= z1_min:
            return False
        return True

    def try_pack(self, cargo, orientation_idx=0):
        """
        尝试将货物装入车厢，实现完整约束检查
        """
        # 1. 获取姿态尺寸
        if orientation_idx >= len(cargo.rotations):
            orientation_idx = 0
        l, w, h = cargo.rotations[orientation_idx]

        # 2. 遍历所有极点
        self.ep_list.sort(key=self._ep_sort_key)
        for ep in self.ep_list:
            pos = (ep[0], ep[1], ep[2])

            # 3. 完整约束检查（按文档顺序）
            # 3.1 越界判定
            if pos[0] + l > self.L or pos[1] + w > self.W or pos[2] + h > self.H:
                continue

            # 3.2 碰撞检测
            overlap = False
            for loaded_cargo, loaded_pos, loaded_rot in self.loaded_items:
                loaded_dim = loaded_cargo.rotations[loaded_rot]
                if self._aabb_overlap(pos, (l, w, h), loaded_pos, loaded_dim):
                    overlap = True
                    break
            if overlap:
                continue

            # 3.3 悬空与重心判定（如果货物不贴地）
            if pos[2] > 0:
                # 找出正下方提供支撑的货物
                supporting_items = []
                total_support_area = 0

                for loaded_cargo, loaded_pos, loaded_rot in self.loaded_items:
                    loaded_dim = loaded_cargo.rotations[loaded_rot]
                    loaded_z_max = loaded_pos[2] + loaded_dim[2]

                    # 刚好在下方且XY投影重叠
                    if abs(loaded_z_max - pos[2]) < 0.1:  # 允许微小误差
                        # 计算重叠矩形
                        x_overlap = max(0, min(pos[0] + l, loaded_pos[0] + loaded_dim[0]) -
                                        max(pos[0], loaded_pos[0]))
                        y_overlap = max(0, min(pos[1] + w, loaded_pos[1] + loaded_dim[1]) -
                                        max(pos[1], loaded_pos[1]))

                        if x_overlap > 0 and y_overlap > 0:
                            support_area = x_overlap * y_overlap
                            supporting_items.append({
                                'cargo': loaded_cargo,
                                'pos': loaded_pos,
                                'dim': loaded_dim,
                                'area': support_area
                            })
                            total_support_area += support_area

                # 如果没有支撑，则悬空（不允许）
                if len(supporting_items) == 0:
                    continue

                # 3.4 易碎品保护：下方有易碎件则不允许
                if any(item['cargo'].is_fragile for item in supporting_items):
                    continue

                # 3.5 重心判定：货物重心必须在支撑多边形内
                cargo_center_x = pos[0] + l / 2
                cargo_center_y = pos[1] + w / 2

                center_supported = False
                for item in supporting_items:
                    sup_pos = item['pos']
                    sup_dim = item['dim']
                    if (sup_pos[0] <= cargo_center_x <= sup_pos[0] + sup_dim[0] and
                            sup_pos[1] <= cargo_center_y <= sup_pos[1] + sup_dim[1]):
                        center_supported = True
                        break

                if not center_supported:
                    continue

                # 3.6 压强限制：计算当前货物对下方的压强
                cargo_weight = cargo.weight
                pressure = cargo_weight / total_support_area * 10000  # 转换为kg/m²
                if pressure > 500:  # 超过500kg/m²
                    continue

            # 4. 所有约束通过，装箱成功
            self.loaded_items.append((cargo, pos, orientation_idx))
            self.used_volume += l * w * h
            self.used_weight += cargo.weight

            # 5. 更新极点列表
            self.ep_list.remove(ep)
            self.ep_list.append((pos[0], pos[1], pos[2] + h))  # 上方点
            self.ep_list.append((pos[0] + l, pos[1], pos[2]))  # 右侧点
            self.ep_list.append((pos[0], pos[1] + w, pos[2]))  # 前方点

            return True, pos

        return False, None

    def get_loading_info(self):
        """返回当前车厢的装载信息"""
        info = {
            'loaded_count': len(self.loaded_items),
            'used_volume': self.used_volume,
            'used_weight': self.used_weight,
            'volume_ratio': self.used_volume / (self.L * self.W * self.H),
            'weight_ratio': self.used_weight / self.max_weight,
            'items': []
        }
        for cargo, pos, rot_idx in self.loaded_items:
            info['items'].append({
                'id': cargo.id,
                'type': cargo.type,
                'position': pos,
                'rotation': cargo.rotations[rot_idx],
                'weight': cargo.weight
            })
        return info