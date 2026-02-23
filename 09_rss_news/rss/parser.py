"""Lesson 09: RSS News Agent - RSS 解析"""

import feedparser
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional
from loguru import logger


@dataclass
class RSSItem:
    """RSS 文章项"""

    title: str
    link: str
    published: Optional[str] = None
    summary: Optional[str] = None
    source: Optional[str] = None


class RSSParser:
    """RSS 解析器"""

    def __init__(self, opml_path: str, max_feeds: int = 10):
        self.opml_path = opml_path
        self.feeds = []
        self.max_feeds = max_feeds

    def load_feeds(self) -> list[dict]:
        """从 OPML 加载订阅源"""
        import xml.etree.ElementTree as ET

        feeds = []
        tree = ET.parse(self.opml_path)
        root = tree.getroot()

        # 遍历 OPML 结构 - 支持 outline 标签
        for outline in root.iter("outline"):
            xml_url = outline.get("xmlUrl")
            if xml_url:
                feeds.append(
                    {
                        "title": outline.get("title", outline.get("text", "Unknown")),
                        "url": xml_url,
                    }
                )

        # 限制数量
        feeds = feeds[: self.max_feeds]

        # 只记录限制后的 feeds
        for f in feeds:
            logger.info(f"[RSS] 加载源: {f['title']}")

        self.feeds = feeds
        return feeds

    def fetch_feed(self, url: str) -> list[RSSItem]:
        """获取单个订阅源的文章"""
        try:
            feed = feedparser.parse(url)
            items = []

            for entry in feed.entries[:10]:  # 只取最新 10 篇
                item = RSSItem(
                    title=entry.get("title", ""),
                    link=entry.get("link", ""),
                    published=entry.get("published", ""),
                    summary=entry.get("summary", ""),
                    source=feed.feed.get("title", ""),
                )
                items.append(item)

            logger.info(
                f"[RSS] {feed.feed.get('title', 'Unknown')} - {len(items)} 篇文章"
            )
            return items

        except Exception as e:
            logger.warning(f"[RSS] 获取失败: {url}, 错误: {e}")
            return []

    def fetch_all(self) -> list[RSSItem]:
        """并行获取所有订阅源的文章"""
        if not self.feeds:
            self.load_feeds()

        all_items = []

        # 使用线程池并行获取
        with ThreadPoolExecutor(max_workers=5) as executor:
            # 提交所有任务
            future_to_feed = {
                executor.submit(self.fetch_feed, feed["url"]): feed
                for feed in self.feeds
            }

            # 收集结果
            for future in as_completed(future_to_feed):
                feed = future_to_feed[future]
                try:
                    items = future.result()
                    all_items.extend(items)
                except Exception as e:
                    logger.warning(f"[RSS] 获取 {feed['title']} 失败: {e}")

        return all_items


__all__ = ["RSSParser", "RSSItem"]
