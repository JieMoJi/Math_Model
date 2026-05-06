import numpy as np
import time
from .Truck import Truck
import random
class HeuristicSolver:
    def __init__(self, cargo_list, truck_type=1):
        self.cargo_list = cargo_list
        self.truck_type = truck_type

    def solve_by_density(self):
        """按密度降序的启发式算法"""
        start_time = time.time()
        sorted_cargos = sorted(self.cargo_list, key=lambda c: c.density, reverse=True)
        truck = Truck(self.truck_type)
        packing_plan = []
        for cargo in sorted_cargos:
            best_position = None
            best_rotation_idx = 0
            best_fitness = -1
            for rot_idx in range(len(cargo.rotations)):
                temp_truck = Truck(self.truck_type)
                temp_truck.loaded_items = truck.loaded_items.copy()
                temp_truck.ep_list = truck.ep_list.copy()
                temp_truck.used_volume = truck.used_volume
                temp_truck.used_weight = truck.used_weight
                success, pos = temp_truck.try_pack(cargo, orientation_idx=rot_idx)
                if success:
                    fitness = self._position_fitness(pos, cargo.rotations[rot_idx])
                    if fitness > best_fitness:
                        best_fitness = fitness
                        best_position = pos
                        best_rotation_idx = rot_idx
            if best_position is not None:
                success, pos = truck.try_pack(cargo, orientation_idx=best_rotation_idx)
                if success:
                    packing_plan.append({
                        'id': cargo.id,
                        'type': cargo.type,
                        'position': pos,
                        'dimensions': cargo.rotations[best_rotation_idx],
                        'weight': cargo.weight,
                        'rotation_idx': best_rotation_idx
                    })
        elapsed = time.time() - start_time
        return truck, packing_plan, elapsed

    def _position_fitness(self, position, dimensions):
        """位置适应度函数：优先低高度、靠角落"""
        x, y, z = position
        l, w, h = dimensions

        # 优先低高度（z越小越好）
        height_penalty = z / 1000

        # 优先靠角落（x,y越小越好）
        corner_penalty = (x + y) / 1000

        # 综合适应度（越小越好，所以取负值）
        fitness = -(height_penalty + corner_penalty)

        return fitness

    def solve_by_volume(self):
        """按体积降序的启发式算法"""
        start_time = time.time()
        sorted_cargos = sorted(self.cargo_list, key=lambda c: c.volume, reverse=True)
        truck = Truck(self.truck_type)
        packing_plan = []
        for cargo in sorted_cargos:
            for rot_idx in range(len(cargo.rotations)):
                success, pos = truck.try_pack(cargo, orientation_idx=rot_idx)
                if success:
                    packing_plan.append({
                        'id': cargo.id,
                        'type': cargo.type,
                        'position': pos,
                        'dimensions': cargo.rotations[rot_idx],
                        'weight': cargo.weight
                    })
                    break
        elapsed = time.time() - start_time
        return truck, packing_plan, elapsed

    def solve_hybrid(self, alpha=0.6, beta=0.4):
        """
        混合启发式算法：同时考虑体积和重量
        alpha: 体积权重, beta: 重量权重
        """
        start_time = time.time()

        # 计算每个货物的综合评分
        for cargo in self.cargo_list:
            # 归一化体积和重量评分
            volume_score = cargo.volume / max(c.volume for c in self.cargo_list)
            weight_score = cargo.weight / max(c.weight for c in self.cargo_list)
            # 综合评分 = alpha*体积分 + beta*重量分
            cargo.composite_score = alpha * volume_score + beta * weight_score

        # 按综合评分降序排序
        sorted_cargos = sorted(self.cargo_list,
                               key=lambda c: c.composite_score,
                               reverse=True)

        truck = Truck(self.truck_type)
        packing_plan = []

        # 第一轮：尝试装所有货物
        for cargo in sorted_cargos:
            best_position = None
            best_rotation_idx = 0
            best_fitness = -1

            # 尝试所有姿态
            for rot_idx in range(len(cargo.rotations)):
                success, pos = truck.try_pack(cargo, orientation_idx=rot_idx)
                if success:
                    # 位置适应度（优先低处）
                    fitness = -pos[2]  # z越小越好
                    if fitness > best_fitness:
                        best_fitness = fitness
                        best_position = pos
                        best_rotation_idx = rot_idx

            if best_position is not None:
                # 重新装箱（确保成功）
                success, pos = truck.try_pack(cargo, orientation_idx=best_rotation_idx)
                if success:
                    packing_plan.append({
                        'id': cargo.id,
                        'type': cargo.type,
                        'position': pos,
                        'dimensions': cargo.rotations[best_rotation_idx],
                        'weight': cargo.weight
                    })

        elapsed = time.time() - start_time

        return truck, packing_plan, elapsed

    def solve_weight_first(self):
        """重量优先算法"""
        start_time = time.time()
        sorted_cargos = sorted(self.cargo_list, key=lambda c: c.weight, reverse=True)
        truck = Truck(self.truck_type)
        packing_plan = []
        # 装重货（重量>=15kg）
        heavy_cargos = [c for c in sorted_cargos if c.weight >= 15]
        for cargo in heavy_cargos:
            for rot_idx in range(len(cargo.rotations)):
                success, pos = truck.try_pack(cargo, orientation_idx=rot_idx)
                if success:
                    packing_plan.append({
                        'id': cargo.id,
                        'type': cargo.type,
                        'position': pos,
                        'dimensions': cargo.rotations[rot_idx],
                        'weight': cargo.weight
                    })
                    break
        # 装轻货（重量<15kg）
        light_cargos = [c for c in sorted_cargos if c.weight < 15]
        for cargo in light_cargos:
            for rot_idx in range(len(cargo.rotations)):
                success, pos = truck.try_pack(cargo, orientation_idx=rot_idx)
                if success:
                    packing_plan.append({
                        'id': cargo.id,
                        'type': cargo.type,
                        'position': pos,
                        'dimensions': cargo.rotations[rot_idx],
                        'weight': cargo.weight
                    })
                    break
        elapsed = time.time() - start_time
        return truck, packing_plan, elapsed

    def solve_balanced(self):
        """
        体积重量平衡算法：专门优化综合满载率
        策略：先装重货铺底，再装轻货填空
        """
        start_time = time.time()

        truck = Truck(self.truck_type)
        packing_plan = []

        # 第一阶段：装重货（重量>10kg）铺底
        heavy_cargos = [c for c in self.cargo_list if c.weight >= 10]
        heavy_cargos.sort(key=lambda c: c.density, reverse=True)  # 密度大的优先

        for cargo in heavy_cargos:
            # 尝试所有姿态，优先高度低的姿态
            rotations_sorted = sorted(range(len(cargo.rotations)),
                                      key=lambda i: cargo.rotations[i][2])  # 按高度排序

            for rot_idx in rotations_sorted:
                success, pos = truck.try_pack(cargo, orientation_idx=rot_idx)
                if success:
                    packing_plan.append({
                        'id': cargo.id,
                        'type': cargo.type,
                        'position': pos,
                        'dimensions': cargo.rotations[rot_idx],
                        'weight': cargo.weight
                    })
                    break

        # 第二阶段：装中等重量货物填空
        medium_cargos = [c for c in self.cargo_list if 5 <= c.weight < 10]
        medium_cargos.sort(key=lambda c: c.volume, reverse=True)  # 体积大的优先

        for cargo in medium_cargos:
            for rot_idx in range(len(cargo.rotations)):
                success, pos = truck.try_pack(cargo, orientation_idx=rot_idx)
                if success:
                    packing_plan.append({
                        'id': cargo.id,
                        'type': cargo.type,
                        'position': pos,
                        'dimensions': cargo.rotations[rot_idx],
                        'weight': cargo.weight
                    })
                    break

        # 第三阶段：装轻货填缝
        light_cargos = [c for c in self.cargo_list if c.weight < 5]
        light_cargos.sort(key=lambda c: c.volume)  # 体积小的优先（填缝）

        for cargo in light_cargos:
            for rot_idx in range(len(cargo.rotations)):
                success, pos = truck.try_pack(cargo, orientation_idx=rot_idx)
                if success:
                    packing_plan.append({
                        'id': cargo.id,
                        'type': cargo.type,
                        'position': pos,
                        'dimensions': cargo.rotations[rot_idx],
                        'weight': cargo.weight
                    })
                    break

        elapsed = time.time() - start_time

        return truck, packing_plan, elapsed

    def solve_layered(self):
        """分层装载算法"""
        start_time = time.time()
        truck = Truck(self.truck_type)
        packing_plan = []
        # 分类
        heavy_cargos = [c for c in self.cargo_list if c.weight >= 20]
        medium_cargos = [c for c in self.cargo_list if 10 <= c.weight < 20]
        light_cargos = [c for c in self.cargo_list if c.weight < 10]
        # 阶段1：装G4重货
        g4_cargos = [c for c in heavy_cargos if c.id.startswith('G4')]
        g4_cargos.sort(key=lambda c: c.volume, reverse=True)
        for cargo in g4_cargos:
            rotations = sorted(range(len(cargo.rotations)), key=lambda i: cargo.rotations[i][2])
            for rot_idx in rotations:
                success, pos = truck.try_pack(cargo, orientation_idx=rot_idx)
                if success:
                    packing_plan.append({
                        'id': cargo.id,
                        'type': cargo.type,
                        'position': pos,
                        'dimensions': cargo.rotations[rot_idx],
                        'weight': cargo.weight
                    })
                    break
        # 阶段2：装中等货物
        medium_all = medium_cargos.copy()
        medium_all.sort(key=lambda c: c.density, reverse=True)
        for cargo in medium_all:
            for rot_idx in range(len(cargo.rotations)):
                success, pos = truck.try_pack(cargo, orientation_idx=rot_idx)
                if success:
                    packing_plan.append({
                        'id': cargo.id,
                        'type': cargo.type,
                        'position': pos,
                        'dimensions': cargo.rotations[rot_idx],
                        'weight': cargo.weight
                    })
                    break
        # 阶段3：装轻货
        light_all = light_cargos.copy()
        light_all.sort(key=lambda c: c.volume)
        for cargo in light_all:
            for rot_idx in range(len(cargo.rotations)):
                success, pos = truck.try_pack(cargo, orientation_idx=rot_idx)
                if success:
                    packing_plan.append({
                        'id': cargo.id,
                        'type': cargo.type,
                        'position': pos,
                        'dimensions': cargo.rotations[rot_idx],
                        'weight': cargo.weight
                    })
                    break
        elapsed = time.time() - start_time
        return truck, packing_plan, elapsed

    def solve_optimized(self):
        """
        优化算法：专门针对题目数据调优
        策略：优先G4(25kg) → G3(15kg) → G5(18kg) → G1(12kg) → G2(8kg)
        """
        start_time = time.time()

        truck = Truck(self.truck_type)
        packing_plan = []

        # 按货物类型分组
        cargo_by_type = {}
        for cargo in self.cargo_list:
            cargo_by_type.setdefault(cargo.id[:2], []).append(cargo)

        # 装载顺序：G4(最重) → G3 → G5 → G1 → G2(最轻)
        load_order = ['G4', 'G3', 'G5', 'G1', 'G2']

        for type_prefix in load_order:
            if type_prefix not in cargo_by_type:
                continue

            cargos = cargo_by_type[type_prefix]
            print(f"  装载{type_prefix}类货物: {len(cargos)}件")

            # 对每类货物，按重量降序
            cargos.sort(key=lambda c: c.weight, reverse=True)

            for cargo in cargos:
                packed = False
                # 尝试所有姿态
                for rot_idx in range(len(cargo.rotations)):
                    success, pos = truck.try_pack(cargo, orientation_idx=rot_idx)
                    if success:
                        packing_plan.append({
                            'id': cargo.id,
                            'type': cargo.type,
                            'position': pos,
                            'dimensions': cargo.rotations[rot_idx],
                            'weight': cargo.weight
                        })
                        packed = True
                        break

                # 如果装不下，跳过此类货物的剩余部分
                if not packed:
                    # 尝试下一个姿态更小的货物
                    continue

        elapsed = time.time() - start_time

        return truck, packing_plan, elapsed

    def solve_height_optimized(self):
        """
        高度优化算法：主动利用车厢高度
        策略：先铺满底层，然后逐层向上堆叠
        """
        start_time = time.time()

        truck = Truck(self.truck_type)
        packing_plan = []

        # 按底面积×重量综合评分排序
        for cargo in self.cargo_list:
            # 评分 = 重量 × 底面积（鼓励重且占地面积大的放底层）
            base_area = cargo.l * cargo.w
            cargo.height_score = cargo.weight * base_area

        # 第一阶段：底层铺重货（评分高的放底层）
        sorted_by_height_score = sorted(self.cargo_list,
                                        key=lambda c: c.height_score,
                                        reverse=True)

        print("  阶段1: 铺底层重货...")
        layer_height = 0
        for cargo in sorted_by_height_score:
            # 只考虑能放在当前层的货物
            if cargo.h > 100:  # 太高的货物先跳过
                continue

            # 尝试所有姿态，优先高度低的
            rotations = sorted(range(len(cargo.rotations)),
                               key=lambda i: cargo.rotations[i][2])
            for rot_idx in rotations:
                success, pos = truck.try_pack(cargo, orientation_idx=rot_idx)
                if success:
                    packing_plan.append({
                        'id': cargo.id,
                        'type': cargo.type,
                        'position': pos,
                        'dimensions': cargo.rotations[rot_idx],
                        'weight': cargo.weight
                    })
                    # 更新当前层高度
                    if pos[2] + cargo.rotations[rot_idx][2] > layer_height:
                        layer_height = pos[2] + cargo.rotations[rot_idx][2]
                    break

        # 第二阶段：中层堆叠（高度50-150cm）
        print("  阶段2: 中层堆叠...")
        remaining_cargos = [c for c in self.cargo_list
                            if c.id not in [p['id'] for p in packing_plan]]

        # 按高度排序，中等高度的优先
        remaining_cargos.sort(key=lambda c: abs(c.h - 80))  # 接近80cm的优先

        for cargo in remaining_cargos:
            for rot_idx in range(len(cargo.rotations)):
                success, pos = truck.try_pack(cargo, orientation_idx=rot_idx)
                if success:
                    packing_plan.append({
                        'id': cargo.id,
                        'type': cargo.type,
                        'position': pos,
                        'dimensions': cargo.rotations[rot_idx],
                        'weight': cargo.weight
                    })
                    break

        # 第三阶段：顶层填空（小件填缝）
        print("  阶段3: 顶层填空...")
        remaining_cargos = [c for c in self.cargo_list
                            if c.id not in [p['id'] for p in packing_plan]]

        # 小体积的优先填缝
        remaining_cargos.sort(key=lambda c: c.volume)

        for cargo in remaining_cargos:
            for rot_idx in range(len(cargo.rotations)):
                success, pos = truck.try_pack(cargo, orientation_idx=rot_idx)
                if success:
                    packing_plan.append({
                        'id': cargo.id,
                        'type': cargo.type,
                        'position': pos,
                        'dimensions': cargo.rotations[rot_idx],
                        'weight': cargo.weight
                    })
                    break

        elapsed = time.time() - start_time

        return truck, packing_plan, elapsed

    def solve_vertical_first(self):
        """
        垂直优先算法：优先利用Z轴高度
        策略：先装高的货物建立垂直结构，再填空
        """
        start_time = time.time()

        truck = Truck(self.truck_type)
        packing_plan = []

        # 第一阶段：装高货物建立垂直结构
        print("  阶段1: 建立垂直结构...")
        tall_cargos = [c for c in self.cargo_list if c.h >= 50]
        tall_cargos.sort(key=lambda c: c.h, reverse=True)  # 最高的优先

        for cargo in tall_cargos:
            # 尝试姿态，优先高度方向与Z轴对齐
            for rot_idx in range(len(cargo.rotations)):
                l, w, h = cargo.rotations[rot_idx]
                if h >= 50:  # 优先高度大的姿态
                    success, pos = truck.try_pack(cargo, orientation_idx=rot_idx)
                    if success:
                        packing_plan.append({
                            'id': cargo.id,
                            'type': cargo.type,
                            'position': pos,
                            'dimensions': cargo.rotations[rot_idx],
                            'weight': cargo.weight
                        })
                        break

        # 第二阶段：装中等高度货物
        print("  阶段2: 填充中层...")
        medium_cargos = [c for c in self.cargo_list
                         if 30 <= c.h < 50 and c.id not in [p['id'] for p in packing_plan]]
        medium_cargos.sort(key=lambda c: c.volume, reverse=True)

        for cargo in medium_cargos:
            for rot_idx in range(len(cargo.rotations)):
                success, pos = truck.try_pack(cargo, orientation_idx=rot_idx)
                if success:
                    packing_plan.append({
                        'id': cargo.id,
                        'type': cargo.type,
                        'position': pos,
                        'dimensions': cargo.rotations[rot_idx],
                        'weight': cargo.weight
                    })
                    break

        # 第三阶段：装矮货物填缝
        print("  阶段3: 底层填缝...")
        short_cargos = [c for c in self.cargo_list
                        if c.h < 30 and c.id not in [p['id'] for p in packing_plan]]
        short_cargos.sort(key=lambda c: c.volume)

        for cargo in short_cargos:
            for rot_idx in range(len(cargo.rotations)):
                success, pos = truck.try_pack(cargo, orientation_idx=rot_idx)
                if success:
                    packing_plan.append({
                        'id': cargo.id,
                        'type': cargo.type,
                        'position': pos,
                        'dimensions': cargo.rotations[rot_idx],
                        'weight': cargo.weight
                    })
                    break

        elapsed = time.time() - start_time

        return truck, packing_plan, elapsed

    def solve_volume_weight_tradeoff(self, target_weight_ratio=0.5):
        """体积-重量权衡算法"""
        start_time = time.time()
        truck = Truck(self.truck_type)
        packing_plan = []
        target_weight = truck.max_weight * target_weight_ratio
        # 阶段1：装重货达到目标重量
        heavy_cargos = [c for c in self.cargo_list if c.weight >= 15]
        heavy_cargos.sort(key=lambda c: c.weight, reverse=True)
        current_weight = 0

        for cargo in heavy_cargos:
            if current_weight >= target_weight:
                break
            for rot_idx in range(len(cargo.rotations)):
                success, pos = truck.try_pack(cargo, orientation_idx=rot_idx)
                if success:
                    packing_plan.append({
                        'id': cargo.id,
                        'type': cargo.type,
                        'position': pos,
                        'dimensions': cargo.rotations[rot_idx],
                        'weight': cargo.weight
                    })
                    current_weight += cargo.weight
                    break
        # 阶段2：装中等货物优化体积
        medium_cargos = [c for c in self.cargo_list
                         if 10 <= c.weight < 15 and c.id not in [p['id'] for p in packing_plan]]
        medium_cargos.sort(key=lambda c: c.volume / c.weight, reverse=True)

        for cargo in medium_cargos:
            for rot_idx in range(len(cargo.rotations)):
                success, pos = truck.try_pack(cargo, orientation_idx=rot_idx)
                if success:
                    packing_plan.append({
                        'id': cargo.id,
                        'type': cargo.type,
                        'position': pos,
                        'dimensions': cargo.rotations[rot_idx],
                        'weight': cargo.weight
                    })
                    break
        # 阶段3：装轻货填空间
        light_cargos = [c for c in self.cargo_list
                        if c.weight < 10 and c.id not in [p['id'] for p in packing_plan]]
        light_cargos.sort(key=lambda c: c.volume, reverse=True)

        for cargo in light_cargos:
            for rot_idx in range(len(cargo.rotations)):
                success, pos = truck.try_pack(cargo, orientation_idx=rot_idx)
                if success:
                    packing_plan.append({
                        'id': cargo.id,
                        'type': cargo.type,
                        'position': pos,
                        'dimensions': cargo.rotations[rot_idx],
                        'weight': cargo.weight
                    })
                    break
        elapsed = time.time() - start_time
        return truck, packing_plan, elapsed

    def solve_iterative_improvement(self, base_plan=None):
        """迭代改进算法（修复参数问题）"""
        start_time = time.time()

        # 修复：如果没有基础方案，先生成一个
        if base_plan is None or len(base_plan) == 0:
            _, base_plan, _ = self.solve_layered()

        # 获取已装货物ID
        packed_ids = [p['id'] for p in base_plan]
        all_cargos = self.cargo_list.copy()
        best_fitness = 0
        best_truck = None
        best_plan = None
        for attempt in range(10):
            temp_truck = Truck(self.truck_type)
            temp_plan = []
            random.shuffle(all_cargos)
            for cargo in all_cargos:
                for rot_idx in range(len(cargo.rotations)):
                    success, pos = temp_truck.try_pack(cargo, orientation_idx=rot_idx)
                    if success:
                        temp_plan.append({
                            'id': cargo.id,
                            'type': cargo.type,
                            'position': pos,
                            'dimensions': cargo.rotations[rot_idx],
                            'weight': cargo.weight
                        })
                        break
            info = temp_truck.get_loading_info()
            fitness = 0.6 * info['volume_ratio'] + 0.4 * info['weight_ratio']
            if fitness > best_fitness:
                best_fitness = fitness
                best_truck = temp_truck
                best_plan = temp_plan
        elapsed = time.time() - start_time
        return best_truck, best_plan, elapsed