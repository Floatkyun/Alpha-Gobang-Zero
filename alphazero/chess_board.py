# coding: utf-8
from typing import Tuple
from copy import deepcopy
from collections import OrderedDict

import torch
import numpy as np


class ChessBoard:
    """ 棋盘类 """

    BLACK = 1
    WHITE = 0
    EMPTY = -1

    def __init__(self, board_len=9, n_feature_planes=9):
        """
        Parameters
        ----------
        board_len: int
            棋盘边长

        n_feature_planes: int
            特征平面的个数，必须为奇数
        """
        if n_feature_planes % 2 == 0:
            raise ValueError("特征平面的个数必须为奇数")
        self.board_len = board_len
        self.current_player = self.BLACK
        self.n_feature_planes = n_feature_planes
        self.available_actions = list(range(self.board_len**2))
        # 棋盘状态字典，key 为 action，value 为 current_player
        self.state = OrderedDict()
        # 上一个落点
        self.previous_action = None

    def copy(self):
        """ 复制棋盘 """
        return deepcopy(self)

    def clear_board(self):
        """ 清空棋盘 """
        self.state.clear()
        self.previous_action = None
        self.current_player = self.BLACK
        self.available_actions = list(range(self.board_len**2))

    def do_action(self, action: int):
        """ 落子并更新棋盘

        Parameters
        ----------
        action: int
            落子位置，范围为 `[0, board_len^2 -1]`
        """
        self.previous_action = action
        self.available_actions.remove(action)
        self.state[action] = self.current_player
        self.current_player = self.WHITE + self.BLACK - self.current_player

    def do_action_(self, pos: tuple) -> bool:
        """ 落子并更新棋盘，只提供给 app 使用

        Parameters
        ----------
        pos: Tuple[int, int]
            落子在棋盘上的位置，范围为 `(0, 0) ~ (board_len-1, board_len-1)`

        Returns
        -------
        update_ok: bool
            是否成功落子
        """
        action = pos[0]*self.board_len + pos[1]
        if action in self.available_actions:
            self.do_action(action)
            return True
        return False

    def is_game_over(self) -> Tuple[bool, int]:
        """ 判断游戏是否结束

        Returns
        -------
        is_over: bool
            游戏是否结束，分出胜负或者平局则为 `True`, 否则为 `False`

        winner: int
            游戏赢家，有以下几种:
            * 如果游戏分出胜负，则为 `ChessBoard.BLACK` 或 `ChessBoard.WHITE`
            * 如果还有分出胜负或者平局，则为 `None`
        """
        # 如果下的棋子不到 9 个，就直接判断游戏还没结束
        if len(self.state) < 9:
            return False, None

        n = self.board_len
        for action, player in self.state.items():
            row, col = action//n, action % n

            # 水平搜索
            if col <= n-5 and len(set(self.state.get(i, self.EMPTY) for i in range(action, action+5))) == 1:
                return True, player

            # 竖直搜索
            if row <= n-5 and len(set(self.state.get(i, self.EMPTY) for i in range(action, action+5*n, n))) == 1:
                return True, player

            # 主对角线方向搜索
            if row <= n-5 and col <= n-5 and len(set(self.state.get(i, self.EMPTY) for i in range(action, action+5*(n+1), n+1))) == 1:
                return True, player

            # 副对角线方向搜索
            if row <= n-5 and col >= 4 and len(set(self.state.get(i, self.EMPTY) for i in range(action, action+5*(n-1), n-1))) == 1:
                return True, player

        # 平局
        if not self.available_actions:
            return True, None

        return False, None

    def get_feature_planes(self) -> torch.Tensor:
        """ 棋盘状态特征张量，维度为 `(9, board_len, board_len)`

        Returns
        -------
        feature_planes: Tensor of shape (9, board_len, board_len)
            特征平面图像
        """
        feature_planes = torch.zeros((9, self.board_len**2))
        # 最后一张图像代表当前玩家颜色
        feature_planes[-1] = self.current_player
        # 添加历史信息
        if self.state:
            actions = np.array(list(self.state.keys()))[::-1]
            players = np.array(list(self.state.values()))[::-1]
            Xt = actions[players == self.current_player]
            Yt = actions[players != self.current_player]
            for i in range(4):
                if i < len(Xt):
                    feature_planes[2*i, Xt[i:]] = 1
                if i < len(Yt):
                    feature_planes[2*i+1, Yt[i:]] = 1
        return feature_planes.view((9, self.board_len, self.board_len))


class ColorError(ValueError):

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
