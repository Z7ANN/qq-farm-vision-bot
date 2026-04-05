"""任务调度器 - 管理自动化任务的执行周期"""
import time
from datetime import datetime
from enum import Enum
from loguru import logger

from PyQt6.QtCore import QObject, QTimer, pyqtSignal


class BotState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ANALYZING = "analyzing"
    EXECUTING = "executing"
    WAITING = "waiting"
    ERROR = "error"


class TaskScheduler(QObject):
    """基于QTimer的任务调度器，与Qt事件循环集成"""

    state_changed = pyqtSignal(str)  # 状态变化信号
    check_triggered = pyqtSignal()  # 检查触发（农场+好友）
    stats_updated = pyqtSignal(dict)  # 统计数据更新

    def __init__(self):
        super().__init__()
        self._state = BotState.IDLE
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer)

        # 统计
        self._start_time: float = 0
        self._stats = {
            "harvest": 0, "plant": 0, "water": 0,
            "weed": 0, "bug": 0, "steal": 0,
            "sell": 0, "total_actions": 0,
        }
        self._next_check: float = 0

    @property
    def state(self) -> BotState:
        return self._state

    def _set_state(self, state: BotState):
        self._state = state
        self.state_changed.emit(state.value)

    def start(self, interval_ms: int = 180000):
        """启动调度器
        
        Args:
            interval_ms: 检查间隔（毫秒），默认180000ms = 3分钟
        """
        if self._state == BotState.RUNNING:
            return
        self._start_time = time.time()
        self._set_state(BotState.RUNNING)

        # 启动定时器
        self._timer.start(interval_ms)
        self._next_check = time.time()

        # 首次立即触发
        QTimer.singleShot(500, self._on_timer)
        logger.info(f"调度器已启动 (检查间隔:{interval_ms//1000}秒)")

    def stop(self):
        """停止调度器"""
        self._timer.stop()
        self._set_state(BotState.IDLE)
        logger.info("调度器已停止")

    def pause(self):
        """暂停"""
        if self._state == BotState.RUNNING:
            self._timer.stop()
            self._set_state(BotState.PAUSED)
            logger.info("调度器已暂停")

    def resume(self):
        """恢复"""
        if self._state == BotState.PAUSED:
            self._timer.start()
            self._set_state(BotState.RUNNING)
            logger.info("调度器已恢复")

    def run_once(self):
        """手动触发一次检查"""
        logger.info("手动触发检查")
        self.check_triggered.emit()

    def set_interval(self, seconds: int):
        """动态调整检查间隔（秒）"""
        ms = max(3000, seconds * 1000)
        self._timer.setInterval(ms)
        self._next_check = time.time() + seconds
        if seconds >= 60:
            logger.info(f"检查间隔调整为 {seconds // 60}分{seconds % 60}秒")
        else:
            logger.info(f"检查间隔调整为 {seconds}秒")

    def _on_timer(self):
        if self._state not in (BotState.RUNNING,):
            return
        self._next_check = time.time() + self._timer.interval() / 1000
        self.check_triggered.emit()

    def record_action(self, action_type: str, count: int = 1):
        """记录操作统计"""
        if action_type in self._stats:
            self._stats[action_type] += count
        self._stats["total_actions"] += count
        self.stats_updated.emit(self.get_stats())

    def get_stats(self) -> dict:
        """获取统计数据"""
        elapsed = time.time() - self._start_time if self._start_time else 0
        hours = int(elapsed // 3600)
        minutes = int((elapsed % 3600) // 60)
        return {
            **self._stats,
            "elapsed": f"{hours}小时{minutes}分",
            "next_check": datetime.fromtimestamp(self._next_check).strftime("%H:%M:%S") if self._next_check else "--",
            "state": self._state.value,
        }

    def reset_stats(self):
        for key in self._stats:
            self._stats[key] = 0

