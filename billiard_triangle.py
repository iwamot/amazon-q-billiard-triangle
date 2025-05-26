#!/usr/bin/env python3
"""
Billiard Triangle Game

Amazon Q CLIを使って開発した、ビリヤード風の三角形ゲーム。
球の物理的な動きを楽しみながら、最終的に3つの球で作られる三角形の面積を競います。

作者: iwamot
開発ツール: Amazon Q CLI
ライセンス: MIT
"""

import pygame
import sys
import math
import random
from pygame.locals import *

# ゲーム設定の定数
SCREEN_WIDTH = 800      # 画面の幅
SCREEN_HEIGHT = 690     # 画面の高さ（UIエリア含む）
BOARD_HEIGHT = 600      # 盤面の高さ
FPS = 60                # フレームレート

# 球の設定
BALL_RADIUS = 15                        # 球の半径
TARGET_BALL_COLOR = (255, 0, 0)         # 的球の色（赤）
PLAYER_BALL_COLOR = (255, 255, 255)     # 手球の色（白）

# 色の設定
BG_COLOR = (0, 100, 0)                  # 盤面の背景色（緑）
UI_BG_COLOR = (50, 50, 50)              # UI部分の背景色（グレー）
TRIANGLE_COLOR = (255, 200, 0, 128)     # 三角形の色（半透明黄色）
TEXT_COLOR = (255, 255, 255)            # テキストの色（白）
INSTRUCTION_COLOR = (255, 255, 0)       # 指示テキストの色（黄色）
FONT_SIZE = 36                          # フォントサイズ

# 物理シミュレーションの定数
FRICTION = 0.99         # 摩擦係数（1に近いほど摩擦が少ない）
MIN_VELOCITY = 0.1      # 停止判定の閾値
INITIAL_SPEED = 22.0    # 球の初速
RESTITUTION = 0.6       # 反発係数（1が完全弾性衝突）
WALL_RESTITUTION = 0.8  # 壁での反発係数


class Ball:
    """
    ビリヤード球のクラス
    位置、速度、色などの属性と、移動や衝突などの機能を持つ
    """
    def __init__(self, x, y, color, is_target=False):
        """
        球の初期化
        
        Args:
            x (float): X座標
            y (float): Y座標
            color (tuple): 球の色 (R,G,B)
            is_target (bool): 的球かどうか
        """
        self.x = x
        self.y = y
        self.vx = 0      # X方向の速度
        self.vy = 0      # Y方向の速度
        self.color = color
        self.is_target = is_target
        self.moving = False
    
    def update(self):
        """球の位置と速度を更新する"""
        if self.moving:
            # 位置の更新
            self.x += self.vx
            self.y += self.vy
            
            # 壁との衝突判定と跳ね返り
            if self.x - BALL_RADIUS < 0:
                self.x = BALL_RADIUS
                self.vx = -self.vx * WALL_RESTITUTION
            elif self.x + BALL_RADIUS > SCREEN_WIDTH:
                self.x = SCREEN_WIDTH - BALL_RADIUS
                self.vx = -self.vx * WALL_RESTITUTION
            
            if self.y - BALL_RADIUS < 0:
                self.y = BALL_RADIUS
                self.vy = -self.vy * WALL_RESTITUTION
            elif self.y + BALL_RADIUS > BOARD_HEIGHT:
                self.y = BOARD_HEIGHT - BALL_RADIUS
                self.vy = -self.vy * WALL_RESTITUTION
            
            # 摩擦による減速
            self.vx *= FRICTION
            self.vy *= FRICTION
            
            # 速度が小さくなったら停止
            if math.sqrt(self.vx**2 + self.vy**2) < MIN_VELOCITY:
                self.vx = 0
                self.vy = 0
                self.moving = False
    
    def move_towards(self, target_x, target_y, speed=INITIAL_SPEED):
        """
        指定した目標に向かって球を移動させる
        
        Args:
            target_x (float): 目標のX座標
            target_y (float): 目標のY座標
            speed (float): 初速
        """
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            self.vx = (dx / distance) * speed
            self.vy = (dy / distance) * speed
            self.moving = True
    
    def collide_with(self, other_ball):
        """
        他の球との衝突判定と反応
        
        Args:
            other_ball (Ball): 衝突相手の球
            
        Returns:
            bool: 衝突したかどうか
        """
        dx = other_ball.x - self.x
        dy = other_ball.y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        
        # 衝突判定
        if distance < BALL_RADIUS * 2:
            # 衝突位置を調整（めり込み防止）
            overlap = BALL_RADIUS * 2 - distance
            if distance > 0:  # ゼロ除算防止
                self.x -= (dx / distance) * (overlap / 2)
                self.y -= (dy / distance) * (overlap / 2)
                other_ball.x += (dx / distance) * (overlap / 2)
                other_ball.y += (dy / distance) * (overlap / 2)
            
            # 衝突後の速度計算（運動量保存則に基づく）
            if distance > 0:  # ゼロ除算防止
                # 衝突の法線方向ベクトル
                nx = dx / distance
                ny = dy / distance
                
                # 相対速度
                dvx = other_ball.vx - self.vx
                dvy = other_ball.vy - self.vy
                
                # 法線方向の相対速度
                dot_product = dvx * nx + dvy * ny
                
                # 衝突による速度変化
                impulse = (1 + RESTITUTION) * dot_product
                
                # 速度の更新
                self.vx += impulse * nx
                self.vy += impulse * ny
                other_ball.vx -= impulse * nx
                other_ball.vy -= impulse * ny
                
                # 両方のボールを動かす
                self.moving = True
                other_ball.moving = True
            
            return True
        
        return False
    
    def draw(self, screen):
        """
        球を画面に描画する
        
        Args:
            screen: 描画対象の画面
        """
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), BALL_RADIUS)


class BilliardTriangleGame:
    """
    ビリヤード三角形ゲームのメインクラス
    ゲームの状態管理、描画、イベント処理などを行う
    """
    def __init__(self):
        """ゲームの初期化"""
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Billiard Triangle Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, FONT_SIZE)
        
        # カーソル用の半透明の球のサーフェスを作成
        self.cursor_ball_surface = pygame.Surface((BALL_RADIUS*2, BALL_RADIUS*2), pygame.SRCALPHA)
        pygame.draw.circle(self.cursor_ball_surface, (255, 255, 255, 128), (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS)
        
        # ベストスコアの初期化
        self.best_score = 0
        
        # ゲーム状態
        self.reset_game()
    
    def reset_game(self):
        """ゲームをリセットし、新しいゲームを開始する"""
        # ターゲット球の初期化（ランダムな位置）
        target_x = random.randint(BALL_RADIUS * 2, SCREEN_WIDTH - BALL_RADIUS * 2)
        target_y = random.randint(BALL_RADIUS * 2, BOARD_HEIGHT - BALL_RADIUS * 2)
        self.target_ball = Ball(target_x, target_y, TARGET_BALL_COLOR, True)
        
        # プレイヤーの球
        self.player_balls = []
        self.balls_left = 2  # 残りの球の数
        
        # ゲーム状態
        self.placing_ball = False  # 球を配置中かどうか
        self.all_balls_stopped = True  # すべての球が停止しているかどうか
        self.game_over = False
        self.current_score = 0
        self.triangle = None
        
        # 一時的な球（配置プレビュー用）
        self.temp_ball = None
    
    def all_stopped(self):
        """
        すべての球が停止しているかチェック
        
        Returns:
            bool: すべての球が停止していればTrue
        """
        if self.target_ball.moving:
            return False
        
        for ball in self.player_balls:
            if ball.moving:
                return False
        
        return True
    
    def update_balls(self):
        """すべての球の位置と速度を更新し、衝突判定を行う"""
        self.target_ball.update()
        
        for ball in self.player_balls:
            ball.update()
            
            # 他の球との衝突チェック
            ball.collide_with(self.target_ball)
            
            for other_ball in self.player_balls:
                if ball != other_ball:
                    ball.collide_with(other_ball)
    
    def calculate_triangle_area(self):
        """
        3つの球で作られる三角形の面積を計算
        
        Returns:
            float: 三角形の面積
        """
        if len(self.player_balls) < 2:
            return 0
        
        p1 = (self.target_ball.x, self.target_ball.y)
        p2 = (self.player_balls[0].x, self.player_balls[0].y)
        p3 = (self.player_balls[1].x, self.player_balls[1].y)
        
        # 三角形の面積を計算（ヘロンの公式）
        a = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        b = math.sqrt((p3[0] - p2[0])**2 + (p3[1] - p2[1])**2)
        c = math.sqrt((p1[0] - p3[0])**2 + (p1[1] - p3[1])**2)
        s = (a + b + c) / 2
        
        # 面積計算の前に三角形が成立するか確認
        if s > 0 and s > a and s > b and s > c:
            area = math.sqrt(s * (s-a) * (s-b) * (s-c))
            self.triangle = [p1, p2, p3]
            return area
        
        return 0
    
    def run(self):
        """ゲームのメインループ"""
        running = True
        
        while running:
            # イベント処理
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False
                    elif event.key == K_r:
                        self.reset_game()
                
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 1 and self.all_stopped() and self.balls_left > 0 and not self.game_over:
                        # マウス位置が盤面内かチェック
                        mouse_pos = pygame.mouse.get_pos()
                        if mouse_pos[1] <= BOARD_HEIGHT:
                            # 他の球と重ならないかチェック
                            can_place = True
                            if math.sqrt((mouse_pos[0] - self.target_ball.x)**2 + (mouse_pos[1] - self.target_ball.y)**2) < BALL_RADIUS * 2:
                                can_place = False
                            
                            for ball in self.player_balls:
                                if math.sqrt((mouse_pos[0] - ball.x)**2 + (mouse_pos[1] - ball.y)**2) < BALL_RADIUS * 2:
                                    can_place = False
                            
                            if can_place:
                                # 球を配置
                                new_ball = Ball(mouse_pos[0], mouse_pos[1], PLAYER_BALL_COLOR)
                                self.placing_ball = True
                                self.player_balls.append(new_ball)
                                self.balls_left -= 1
                
                elif event.type == MOUSEBUTTONUP:
                    if event.button == 1 and self.placing_ball:
                        self.placing_ball = False
                        # 最後に追加した球をターゲット球に向かって移動させる
                        if self.player_balls:
                            last_ball = self.player_balls[-1]
                            # 色が変わる問題を修正するため、明示的に色を設定
                            last_ball.color = PLAYER_BALL_COLOR
                            last_ball.move_towards(self.target_ball.x, self.target_ball.y)
                            self.all_balls_stopped = False
                
                elif event.type == MOUSEMOTION:
                    # マウスの位置に応じて一時的な球の位置を更新
                    mouse_pos = pygame.mouse.get_pos()
                    if mouse_pos[1] <= BOARD_HEIGHT and self.all_stopped() and self.balls_left > 0 and not self.game_over:
                        # 他の球と重ならないかチェック
                        can_place = True
                        if math.sqrt((mouse_pos[0] - self.target_ball.x)**2 + (mouse_pos[1] - self.target_ball.y)**2) < BALL_RADIUS * 2:
                            can_place = False
                        
                        for ball in self.player_balls:
                            if math.sqrt((mouse_pos[0] - ball.x)**2 + (mouse_pos[1] - ball.y)**2) < BALL_RADIUS * 2:
                                can_place = False
                        
                        # 一時的な球を更新
                        if can_place:
                            self.temp_ball = Ball(mouse_pos[0], mouse_pos[1], PLAYER_BALL_COLOR)
                        else:
                            self.temp_ball = None
            
            # 球の更新
            if not self.all_balls_stopped:
                self.update_balls()
                self.all_balls_stopped = self.all_stopped()
                
                # すべての球が停止したら次のステップへ
                if self.all_balls_stopped:
                    if self.balls_left == 0:
                        # ゲーム終了、スコア計算
                        self.current_score = self.calculate_triangle_area()
                        if self.current_score > self.best_score:
                            self.best_score = self.current_score
                        self.game_over = True
            
            # 描画処理
            self._draw_game()
            
            # フレームレートの制限
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()
    
    def _draw_game(self):
        """ゲーム画面の描画"""
        # 背景の描画
        self.screen.fill(UI_BG_COLOR)
        pygame.draw.rect(self.screen, BG_COLOR, (0, 0, SCREEN_WIDTH, BOARD_HEIGHT))
        pygame.draw.line(self.screen, TEXT_COLOR, (0, BOARD_HEIGHT), (SCREEN_WIDTH, BOARD_HEIGHT), 2)
        
        # 三角形の描画
        if self.game_over and self.triangle:
            triangle_surface = pygame.Surface((SCREEN_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(triangle_surface, TRIANGLE_COLOR, self.triangle)
            self.screen.blit(triangle_surface, (0, 0))
        
        # すべての球を描画
        self.target_ball.draw(self.screen)
        for ball in self.player_balls:
            ball.draw(self.screen)
        
        # 一時的な球（プレビュー）を描画
        if self.temp_ball and not self.placing_ball and self.all_balls_stopped and self.balls_left > 0:
            temp_surface = pygame.Surface((BALL_RADIUS*2, BALL_RADIUS*2), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, (255, 255, 255, 128), (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS)
            self.screen.blit(temp_surface, (self.temp_ball.x - BALL_RADIUS, self.temp_ball.y - BALL_RADIUS))
        
        # 情報表示
        self._draw_ui()
        
        # 画面の更新
        pygame.display.flip()
    
    def _draw_ui(self):
        """UI部分の描画"""
        info_y = BOARD_HEIGHT + 15
        
        # スコア表示
        score_text = self.font.render(f"Score: {int(self.current_score)}", True, TEXT_COLOR)
        self.screen.blit(score_text, (20, info_y))
        
        best_score_text = self.font.render(f"Best: {int(self.best_score)}", True, TEXT_COLOR)
        self.screen.blit(best_score_text, (20, info_y + 35))
        
        # ゲームステータスのテキスト
        if self.game_over:
            game_over_text = self.font.render("Press R to play again", True, INSTRUCTION_COLOR)
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, BOARD_HEIGHT // 2))
            self.screen.blit(game_over_text, text_rect)
        elif not self.game_over and self.all_balls_stopped and self.balls_left > 0:
            help_text = self.font.render("Click to place a ball", True, INSTRUCTION_COLOR)
            text_rect = help_text.get_rect(center=(SCREEN_WIDTH // 2, BOARD_HEIGHT // 2))
            self.screen.blit(help_text, text_rect)


if __name__ == "__main__":
    game = BilliardTriangleGame()
    game.run()
