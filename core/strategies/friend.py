"""P4 社交 — 好友巡查/帮忙/偷菜/同意好友"""
import time
from loguru import logger

from models.farm_state import ActionType
from core.cv_detector import DetectResult
from core.scene_detector import Scene, identify_scene
from core.strategies.base import BaseStrategy


class FriendStrategy(BaseStrategy):

    def try_friend_help(self, rect: tuple, detections: list[DetectResult]) -> list[str]:
        """检测好友求助并进入帮忙"""
        btn = self.find_by_name(detections, "btn_friend_help")
        if not btn:
            return []
        
        logger.info("好友帮忙: 检测到好友求助按钮，点击进入")
        self.click(btn.x, btn.y, "好友求助")
        time.sleep(1.0)  # 等待页面切换
        return self._help_in_friend_farm(rect)

    def _help_in_friend_farm(self, rect: tuple) -> list[str]:
        """在好友家园执行帮忙操作：收获 > 除虫 > 除草 > 浇水"""
        actions_done = []
        max_iterations = 20  # 最多循环20次，避免死循环
        
        for iteration in range(max_iterations):
            if self.stopped:
                break
                
            cv_img, dets, _ = self.capture(rect)
            if cv_img is None:
                break

            scene = identify_scene(dets, self.cv_detector, cv_img)
            logger.debug(f"好友帮忙: 第{iteration+1}次检测，场景={scene.value}")

            # 处理弹窗
            if scene == Scene.POPUP:
                from core.strategies.popup import PopupStrategy
                ps = PopupStrategy(self.cv_detector)
                ps.action_executor = self.action_executor
                ps.handle_popup(dets)
                time.sleep(0.5)
                continue

            # 已回到自己农场
            if scene == Scene.FARM_OVERVIEW:
                logger.info("好友帮忙: 已返回自己农场")
                break

            # 在好友农场
            if scene == Scene.FRIEND_FARM:
                acted = False
                
                # 按优先级检测并点击按钮：收获 > 除虫 > 除草 > 浇水
                for btn_name, desc, action_type in [
                    ("btn_harvest", "帮好友收获", ActionType.STEAL),
                    ("btn_bug", "帮好友除虫", ActionType.HELP_BUG),
                    ("btn_weed", "帮好友除草", ActionType.HELP_WEED),
                    ("btn_water", "帮好友浇水", ActionType.HELP_WATER),
                ]:
                    btn = self.find_by_name(dets, btn_name)
                    if btn:
                        logger.info(f"好友帮忙: 执行 {desc}")
                        self.click(btn.x, btn.y, desc, action_type)
                        actions_done.append(desc)
                        acted = True
                        time.sleep(0.8)  # 等待操作完成
                        break

                # 没有可执行的操作，点击回家
                if not acted:
                    home = self.find_by_name(dets, "btn_home")
                    if home:
                        logger.info("好友帮忙: 无更多操作，点击回家")
                        self.click(home.x, home.y, "回家")
                        actions_done.append("回家")
                        time.sleep(0.8)
                        break
                    else:
                        # 找不到回家按钮，尝试点击空白区域返回
                        logger.warning("好友帮忙: 未找到回家按钮，点击空白区域")
                        self.click_blank(rect)
                        time.sleep(0.5)
                        break
            else:
                # 未知场景，等待
                time.sleep(0.5)

        if actions_done:
            logger.info(f"好友帮忙: 完成操作 {len(actions_done)} 项: {', '.join(actions_done)}")
        else:
            logger.info("好友帮忙: 未执行任何操作")
            
        return actions_done

    def try_steal(self, rect: tuple) -> str | None:
        """自动偷菜（待实现：需要进入好友农场检测成熟作物）"""
        # TODO: 好友列表 → 进入 → 检测成熟 → 偷菜 → 回家
        return None

    def try_accept_friend(self, detections: list[DetectResult]) -> str | None:
        """自动同意好友申请（待实现：需要 btn_accept_friend 模板）"""
        # TODO: 检测好友申请弹窗 → 点击同意
        return None


    def try_steal(self, rect: tuple) -> str | None:
        """自动偷菜（待实现：需要进入好友农场检测成熟作物）"""
        # TODO: 好友列表 → 进入 → 检测成熟 → 偷菜 → 回家
        return None

    def try_accept_friend(self, detections: list[DetectResult]) -> str | None:
        """自动同意好友申请（待实现：需要 btn_accept_friend 模板）"""
        # TODO: 检测好友申请弹窗 → 点击同意
        return None
