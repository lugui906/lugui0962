import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

class FlightGame:
    def __init__(self):
        # 初始化Pygame
        pygame.init()
        self.display = (800, 600)
        pygame.display.set_mode(self.display, DOUBLEBUF | OPENGL)
        pygame.display.set_caption('3D 模拟飞行游戏')
        
        # 设置OpenGL
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        gluPerspective(45, (self.display[0]/self.display[1]), 0.1, 500.0)
        glMatrixMode(GL_MODELVIEW)
        
        # 初始化游戏状态
        self.clock = pygame.time.Clock()
        self.running = True
        self.crashed = False
        self.crash_effect = 0
        
        # 相机位置
        self.camera_pos = [0, 5, -15]
        
        # 飞机状态
        self.plane_pos = [0, 0, 0]
        self.plane_rotation = [0, 0, 0]  # 俯仰, 滚转, 偏航
        self.speed = 0.0
        self.throttle = 0.0
        
        # 物理参数
        self.gravity = 0.05
        self.max_speed = 2.0
        self.acceleration = 0.01
        self.crash_speed_threshold = 1.0  # 坠机速度阈值
        self.crash_rotation_threshold = 60.0  # 坠机翻滚角度阈值
        
        # 机场位置
        self.airport_pos = [0, -5, 50]
        
        # 初始化场景对象
        self.trees = []
        self.flowers = []
        self.generate_vegetation()
        
    def handle_events(self):
        """处理游戏事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
        # 处理按键
        keys = pygame.key.get_pressed()
        
        # 重新开始游戏
        if keys[K_r]:
            self.reset_game()
            return
        
        # 如果已坠机，只响应重新开始键
        if self.crashed:
            return
        
        # 控制灵敏度设置 - 分别调整不同轴的灵敏度
        yaw_speed = 0.3  # 偏航速度
        pitch_speed = 0.5  # 增加俯仰速度，使上下摆动更明显
        roll_speed = 0.3  # 滚转速度
        throttle_speed = 0.005  # 降低油门变化速度
        
        # 油门控制 - 更平滑的油门变化
        if keys[K_UP]:
            self.throttle = min(1.0, self.throttle + throttle_speed)
        if keys[K_DOWN]:
            self.throttle = max(0.0, self.throttle - throttle_speed)
        
        # 方向控制 - 差异化灵敏度
        if keys[K_LEFT]:
            self.plane_rotation[2] += yaw_speed  # 偏航
        if keys[K_RIGHT]:
            self.plane_rotation[2] -= yaw_speed
        if keys[K_w]:
            self.plane_rotation[0] -= pitch_speed  # 俯仰 - 增加灵敏度
        if keys[K_s]:
            self.plane_rotation[0] += pitch_speed
        if keys[K_a]:
            self.plane_rotation[1] += roll_speed  # 滚转
        if keys[K_d]:
            self.plane_rotation[1] -= roll_speed
    
    def reset_game(self):
        """重置游戏状态"""
        # 重置飞机状态
        self.plane_pos = [0, 0, 0]
        self.plane_rotation = [0, 0, 0]
        self.speed = 0.0
        self.throttle = 0.0
        self.crashed = False
        self.crash_effect = 0
        
        # 重新生成植被
        self.trees = []
        self.flowers = []
        self.generate_vegetation()
    
    def update_physics(self):
        """更新物理状态"""
        if self.crashed:
            # 坠机后效果
            self.crash_effect += 0.1
            # 飞机残骸旋转
            self.plane_rotation[1] += 1.0
            return
        
        # 应用油门 - 平滑加速
        target_speed = self.throttle * self.max_speed
        self.speed += (target_speed - self.speed) * self.acceleration
        # 限制速度上限
        self.speed = min(self.speed, self.max_speed * 1.1)
        self.speed = max(self.speed, 0.0)
        
        # 应用旋转阻尼 - 分别调整不同轴的阻尼，增强俯仰可控性
        roll_damping = 0.98  # 滚转阻尼保持较大
        pitch_damping = 0.995  # 俯仰阻尼减小，使上下摆动更明显
        self.plane_rotation[0] *= pitch_damping  # 俯仰阻尼
        self.plane_rotation[1] *= roll_damping  # 滚转阻尼
        
        # 限制旋转角度范围，避免过大角度导致失控
        max_rotation = 80.0
        self.plane_rotation[0] = max(-max_rotation, min(max_rotation, self.plane_rotation[0]))  # 俯仰限制
        self.plane_rotation[1] = max(-max_rotation, min(max_rotation, self.plane_rotation[1]))  # 滚转限制
        # 偏航可以360度旋转，所以取模
        self.plane_rotation[2] %= 360.0
        
        # 根据旋转计算前向向量（正确的旋转顺序：偏航→俯仰）
        yaw_rad = np.radians(self.plane_rotation[2])
        pitch_rad = np.radians(self.plane_rotation[0])
        
        # 计算前向向量
        forward = np.array([
            np.sin(yaw_rad) * np.cos(pitch_rad),
            np.sin(pitch_rad),
            np.cos(yaw_rad) * np.cos(pitch_rad)
        ])
        
        # 计算移动距离向量
        movement = forward * self.speed
        
        # 将numpy数组转换为Python列表，避免类型错误
        movement_list = movement.tolist()
        
        # 更新位置
        self.plane_pos[0] += movement_list[0]
        self.plane_pos[1] += movement_list[1]
        self.plane_pos[2] += movement_list[2]
        
        # 应用重力 - 降低重力值，使飞机更容易起飞
        self.plane_pos[1] -= self.gravity * 0.5
        
        # 限制位置范围，避免坐标溢出
        max_pos = 200.0
        self.plane_pos[0] = max(-max_pos, min(max_pos, self.plane_pos[0]))
        self.plane_pos[2] = max(-max_pos, min(max_pos, self.plane_pos[2]))
        
        # 碰撞检测 - 地面
        if self.plane_pos[1] < -5:
            self.plane_pos[1] = -5
            
            # 坠机检测
            if self.speed > self.crash_speed_threshold or \
               abs(self.plane_rotation[0]) > self.crash_rotation_threshold or \
               abs(self.plane_rotation[1]) > self.crash_rotation_threshold:
                self.crashed = True
            else:
                # 安全着陆
                self.speed *= 0.3  # 着陆减速
                # 着陆后稳定飞机
                self.plane_rotation[0] *= 0.5
                self.plane_rotation[1] *= 0.5
    
    def get_height(self):
        """获取当前高度"""
        return max(0, self.plane_pos[1] + 5)  # 地面高度为-5
    
    def generate_vegetation(self):
        """生成随机的花草树木"""
        import random
        
        # 生成树木 - 10棵随机分布的树
        for _ in range(10):
            x = random.randint(-50, 50)
            z = random.randint(-50, 100)
            if abs(x) > 10 or abs(z - 50) > 10:  # 避开机场区域
                self.trees.append([x, -5, z])
        
        # 生成花草 - 20朵随机分布的花
        for _ in range(20):
            x = random.randint(-50, 50)
            z = random.randint(-50, 100)
            if abs(x) > 15 or abs(z - 50) > 15:  # 避开机场区域
                self.flowers.append([x, -5, z, random.random(), random.random(), random.random()])
    
    def draw_plane(self):
        """绘制飞机模型"""
        glPushMatrix()
        
        # 应用位置
        glTranslatef(*self.plane_pos)
        
        # 应用旋转 - 正确的欧拉角顺序：偏航→俯仰→滚转
        glRotatef(self.plane_rotation[2], 0, 1, 0)  # 偏航（Y轴）
        glRotatef(self.plane_rotation[0], 1, 0, 0)  # 俯仰（X轴）
        glRotatef(self.plane_rotation[1], 0, 0, 1)  # 滚转（Z轴）
        
        # 绘制飞机 - 改进的几何体，更清晰可见
        glLineWidth(2.0)  # 增加线宽，提高可见性
        
        # 绘制飞机主体（使用线框模式增强可见性）
        glBegin(GL_LINES)
        glColor3f(1.0, 1.0, 1.0)  # 白色线框
        
        # 机身框架
        glVertex3f(0, 0, 2)
        glVertex3f(-1, 0, -2)
        glVertex3f(0, 0, 2)
        glVertex3f(1, 0, -2)
        glVertex3f(-1, 0, -2)
        glVertex3f(1, 0, -2)
        
        # 机翼框架
        glVertex3f(0, 0, 0)
        glVertex3f(-3, 0, -1)
        glVertex3f(0, 0, 0)
        glVertex3f(3, 0, -1)
        glVertex3f(-3, 0, -1)
        glVertex3f(3, 0, -1)
        
        # 尾翼框架
        glVertex3f(0, 1, -2)
        glVertex3f(-1, 0, -2)
        glVertex3f(0, 1, -2)
        glVertex3f(1, 0, -2)
        
        # 垂直尾翼
        glVertex3f(0, 0, -2)
        glVertex3f(0, 1.5, -2)
        
        # 水平尾翼
        glVertex3f(0, 0.5, -2)
        glVertex3f(-1.5, 0.5, -2)
        glVertex3f(0, 0.5, -2)
        glVertex3f(1.5, 0.5, -2)
        glEnd()
        
        # 绘制飞机实体部分
        glBegin(GL_TRIANGLES)
        # 机身 - 红色
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0, 0, 2)
        glVertex3f(-1, 0, -2)
        glVertex3f(1, 0, -2)
        
        # 左翼 - 蓝色
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0, 0, 0)
        glVertex3f(-3, 0, -1)
        glVertex3f(0, 0.1, -1)
        
        # 右翼 - 蓝色
        glVertex3f(0, 0, 0)
        glVertex3f(3, 0, -1)
        glVertex3f(0, 0.1, -1)
        
        # 尾翼 - 绿色
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0, 1, -2)
        glVertex3f(-1, 0, -2)
        glVertex3f(1, 0, -2)
        glEnd()
        
        glLineWidth(1.0)  # 恢复默认线宽
        glPopMatrix()
    
    def draw_environment(self):
        """绘制游戏环境"""
        # 绘制地面 - 扩展更大范围
        glBegin(GL_QUADS)
        glColor3f(0.2, 0.8, 0.2)
        for i in range(-100, 100, 4):
            for j in range(-100, 150, 4):
                glVertex3f(i, -5, j)
                glVertex3f(i+4, -5, j)
                glVertex3f(i+4, -5, j+4)
                glVertex3f(i, -5, j+4)
        glEnd()
        
        # 绘制机场跑道
        self.draw_airport()
        
        # 绘制树木
        self.draw_trees()
        
        # 绘制花草
        self.draw_flowers()
        
        # 绘制天空（简单背景）
        glBegin(GL_QUADS)
        glColor3f(0.5, 0.7, 1.0)
        glVertex3f(-200, 100, -200)
        glVertex3f(200, 100, -200)
        glVertex3f(200, 100, 200)
        glVertex3f(-200, 100, 200)
        glEnd()
    
    def draw_airport(self):
        """绘制机场和跑道"""
        # 跑道 - 灰色长方形
        glBegin(GL_QUADS)
        glColor3f(0.5, 0.5, 0.5)
        # 主跑道
        glVertex3f(-15, -4.9, 30)
        glVertex3f(15, -4.9, 30)
        glVertex3f(15, -4.9, 70)
        glVertex3f(-15, -4.9, 70)
        # 跑道中心线
        glColor3f(1.0, 1.0, 1.0)
        glVertex3f(-2, -4.8, 30)
        glVertex3f(2, -4.8, 30)
        glVertex3f(2, -4.8, 70)
        glVertex3f(-2, -4.8, 70)
        glEnd()
        
        # 机场停机坪
        glBegin(GL_QUADS)
        glColor3f(0.3, 0.3, 0.3)
        glVertex3f(-30, -4.9, 40)
        glVertex3f(30, -4.9, 40)
        glVertex3f(30, -4.9, 60)
        glVertex3f(-30, -4.9, 60)
        glEnd()
        
        # 机场标识
        glBegin(GL_TRIANGLES)
        glColor3f(1.0, 0.0, 0.0)
        # 风向袋
        glVertex3f(0, -3, 35)
        glVertex3f(0, -3, 38)
        glVertex3f(2, -3, 36.5)
        glEnd()
    
    def draw_trees(self):
        """绘制树木"""
        for tree in self.trees:
            glPushMatrix()
            glTranslatef(tree[0], tree[1], tree[2])
            
            # 树干
            glBegin(GL_QUADS)
            glColor3f(0.4, 0.2, 0.0)
            glVertex3f(-0.5, 0, -0.5)
            glVertex3f(0.5, 0, -0.5)
            glVertex3f(0.5, 2, -0.5)
            glVertex3f(-0.5, 2, -0.5)
            
            glVertex3f(0.5, 0, -0.5)
            glVertex3f(0.5, 0, 0.5)
            glVertex3f(0.5, 2, 0.5)
            glVertex3f(0.5, 2, -0.5)
            
            glVertex3f(0.5, 0, 0.5)
            glVertex3f(-0.5, 0, 0.5)
            glVertex3f(-0.5, 2, 0.5)
            glVertex3f(0.5, 2, 0.5)
            
            glVertex3f(-0.5, 0, 0.5)
            glVertex3f(-0.5, 0, -0.5)
            glVertex3f(-0.5, 2, -0.5)
            glVertex3f(-0.5, 2, 0.5)
            glEnd()
            
            # 树冠
            glBegin(GL_TRIANGLES)
            glColor3f(0.0, 0.6, 0.0)
            # 多层树冠
            for i in range(3):
                y = 2 + i
                size = 3 - i
                glVertex3f(0, y + size, 0)
                glVertex3f(-size, y, -size)
                glVertex3f(size, y, -size)
                
                glVertex3f(0, y + size, 0)
                glVertex3f(size, y, -size)
                glVertex3f(size, y, size)
                
                glVertex3f(0, y + size, 0)
                glVertex3f(size, y, size)
                glVertex3f(-size, y, size)
                
                glVertex3f(0, y + size, 0)
                glVertex3f(-size, y, size)
                glVertex3f(-size, y, -size)
            glEnd()
            
            glPopMatrix()
    
    def draw_flowers(self):
        """绘制花草"""
        for flower in self.flowers:
            glPushMatrix()
            glTranslatef(flower[0], flower[1], flower[2])
            
            # 花茎
            glBegin(GL_LINES)
            glColor3f(0.0, 0.8, 0.0)
            glVertex3f(0, 0, 0)
            glVertex3f(0, 0.5, 0)
            glEnd()
            
            # 花瓣
            glBegin(GL_TRIANGLE_FAN)
            glColor3f(flower[3], flower[4], flower[5])  # 随机颜色
            glVertex3f(0, 0.5, 0)  # 花心
            for i in range(13):
                angle = i * 30
                glVertex3f(
                    0.2 * np.sin(np.radians(angle)),
                    0.5,
                    0.2 * np.cos(np.radians(angle))
                )
            glEnd()
            
            glPopMatrix()
    
    def draw_ui(self):
        """绘制游戏UI"""
        # 设置2D模式
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, self.display[0], 0, self.display[1])
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # 禁用深度测试和光照
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        
        # 使用Pygame绘制文本 - 确保字体加载正确
        try:
            font = pygame.font.Font(None, 28)  # 调整为更合适的大小
            small_font = pygame.font.Font(None, 20)
        except Exception as e:
            font = pygame.font.SysFont('Arial', 28)
            small_font = pygame.font.SysFont('Arial', 20)
        
        # 绘制顺序：先背景，再文本
        
        # 1. 绘制飞行数据仪表盘
        # 背景框
        glColor4f(0.0, 0.0, 0.0, 0.8)  # 更深的透明度
        glBegin(GL_QUADS)
        left = 20
        top = 20
        width = 280
        height = 180
        glVertex2f(left, top)
        glVertex2f(left + width, top)
        glVertex2f(left + width, top + height)
        glVertex2f(left, top + height)
        glEnd()
        
        # 标题
        title = font.render("飞行仪表盘", True, (255, 255, 0))
        title_data = pygame.image.tostring(title, "RGBA", True)
        glWindowPos2f(left + 20, top + 10)
        glDrawPixels(title.get_width(), title.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, title_data)
        
        # 绘制游戏数据
        ui_data = [
            f"速度: {self.speed:.2f}",
            f"高度: {self.get_height():.1f}",
            f"油门: {self.throttle:.0%}",
            f"俯仰: {self.plane_rotation[0]:.1f}°",
            f"滚转: {self.plane_rotation[1]:.1f}°",
            f"偏航: {self.plane_rotation[2]:.1f}°"
        ]
        
        # 如果坠机，显示坠机信息
        if self.crashed:
            ui_data.append("")
            ui_data.append("=== 坠机! ===")
            ui_data.append("按R键重新开始")
        
        # 渲染飞行数据
        glColor3f(1.0, 1.0, 1.0)
        for i, text in enumerate(ui_data):
            text_surface = font.render(text, True, (255, 255, 255))
            text_data = pygame.image.tostring(text_surface, "RGBA", True)
            # 计算正确的位置，确保文本在背景框内
            pos_x = left + 20
            pos_y = top + 50 + i * 25  # 调整行间距
            glWindowPos2f(pos_x, pos_y)
            glDrawPixels(text_surface.get_width(), text_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        
        # 2. 绘制控制按钮说明
        # 背景框
        glColor4f(0.0, 0.0, 0.0, 0.8)
        left2 = self.display[0] - 290
        top2 = 20
        width2 = 270
        height2 = 200
        glBegin(GL_QUADS)
        glVertex2f(left2, top2)
        glVertex2f(left2 + width2, top2)
        glVertex2f(left2 + width2, top2 + height2)
        glVertex2f(left2, top2 + height2)
        glEnd()
        
        # 控制说明标题
        control_title = font.render("控制说明", True, (255, 255, 0))
        control_title_data = pygame.image.tostring(control_title, "RGBA", True)
        glWindowPos2f(left2 + 70, top2 + 10)
        glDrawPixels(control_title.get_width(), control_title.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, control_title_data)
        
        # 渲染控制说明
        controls = [
            "↑ / ↓ : 增减油门",
            "← / → : 左右转向",
            "W / S : 上下俯仰",
            "A / D : 左右滚转",
            "",
            "起飞步骤:",
            "1. 按↑增加油门",
            "2. 按W抬起机头"
        ]
        
        for i, control in enumerate(controls):
            control_surface = small_font.render(control, True, (255, 255, 255))
            control_data = pygame.image.tostring(control_surface, "RGBA", True)
            pos_x2 = left2 + 20
            pos_y2 = top2 + 50 + i * 22  # 调整行间距
            glWindowPos2f(pos_x2, pos_y2)
            glDrawPixels(control_surface.get_width(), control_surface.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, control_data)
        
        # 3. 绘制简单的控制按钮模拟
        # 油门控制模拟
        glColor4f(0.2, 0.2, 0.2, 0.9)
        throttle_left = left + 20
        throttle_top = top + height + 20
        throttle_width = 200
        throttle_height = 30
        glBegin(GL_QUADS)
        glVertex2f(throttle_left, throttle_top)
        glVertex2f(throttle_left + throttle_width, throttle_top)
        glVertex2f(throttle_left + throttle_width, throttle_top + throttle_height)
        glVertex2f(throttle_left, throttle_top + throttle_height)
        glEnd()
        
        # 油门指示器
        glColor4f(0.0, 1.0, 0.0, 1.0)
        indicator_width = throttle_width * self.throttle
        glBegin(GL_QUADS)
        glVertex2f(throttle_left, throttle_top)
        glVertex2f(throttle_left + indicator_width, throttle_top)
        glVertex2f(throttle_left + indicator_width, throttle_top + throttle_height)
        glVertex2f(throttle_left, throttle_top + throttle_height)
        glEnd()
        
        # 油门标签
        throttle_label = small_font.render(f"油门: {self.throttle:.0%}", True, (255, 255, 255))
        throttle_label_data = pygame.image.tostring(throttle_label, "RGBA", True)
        glWindowPos2f(throttle_left + 10, throttle_top + 5)
        glDrawPixels(throttle_label.get_width(), throttle_label.get_height(), GL_RGBA, GL_UNSIGNED_BYTE, throttle_label_data)
        
        # 恢复3D模式设置
        glEnable(GL_DEPTH_TEST)
        # 保持光照禁用，因为当前场景没有配置光照
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    
    def render(self):
        """渲染游戏场景"""
        # 重置OpenGL状态
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_COLOR_MATERIAL)
        glDisable(GL_LIGHTING)  # 简化渲染，避免光照问题
        
        # 清除屏幕
        glClearColor(0.5, 0.7, 1.0, 1.0)  # 设置天空蓝色背景
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # 重置模型视图矩阵
        glLoadIdentity()
        
        # 相机跟随飞机 - 始终从飞机后方一定距离观察
        camera_distance = 15.0
        camera_height = 5.0
        
        # 根据飞机位置和旋转计算相机位置
        yaw_rad = np.radians(self.plane_rotation[2])
        camera_x = self.plane_pos[0] - np.sin(yaw_rad) * camera_distance
        camera_z = self.plane_pos[2] - np.cos(yaw_rad) * camera_distance
        camera_y = self.plane_pos[1] + camera_height
        
        # 确保相机位置有效
        camera_x = float(camera_x)
        camera_y = float(camera_y)
        camera_z = float(camera_z)
        
        # 设置相机位置并指向飞机
        gluLookAt(
            camera_x, camera_y, camera_z,  # 相机位置
            self.plane_pos[0], self.plane_pos[1], self.plane_pos[2],  # 看向飞机
            0, 1, 0  # 上方向
        )
        
        # 绘制环境
        self.draw_environment()
        
        # 绘制飞机
        self.draw_plane()
        
        # 绘制UI
        self.draw_ui()
        
        # 更新显示
        pygame.display.flip()
    
    def run(self):
        """运行游戏主循环"""
        while self.running:
            self.handle_events()
            self.update_physics()
            self.render()
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    game = FlightGame()
    game.run()