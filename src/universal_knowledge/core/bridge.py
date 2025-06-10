"""
Bridge Adapter - ツール間連携アーキテクチャ
Tool Integration Architecture with Bridge Adapter Pattern
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from datetime import datetime
import json
from dataclasses import dataclass, asdict


@dataclass
class StandardProjectData:
    """標準プロジェクトデータフォーマット"""
    name: str
    description: str
    path: str
    type: str
    created_at: str
    last_modified: str
    metadata: Dict[str, Any]
    files: List[Dict[str, str]]
    tasks: List[Dict[str, Any]]
    tags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StandardProjectData':
        """辞書から生成"""
        return cls(**data)


class ToolAdapter(ABC):
    """
    ツールアダプターの抽象基底クラス
    外部ツールとの連携を標準化するインターフェース
    """
    
    def __init__(self, name: str):
        self.name = name
        self._connected = False
        self._config = {}
    
    @abstractmethod
    def connect(self, config: Dict[str, Any]) -> bool:
        """
        ツールに接続
        
        Args:
            config: 接続設定
            
        Returns:
            bool: 接続成功可否
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """
        ツールから切断
        
        Returns:
            bool: 切断成功可否
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        接続状態を確認
        
        Returns:
            bool: 接続状態
        """
        pass
    
    @abstractmethod
    def sync_data(self, project_data: StandardProjectData) -> bool:
        """
        プロジェクトデータを同期
        
        Args:
            project_data: 標準プロジェクトデータ
            
        Returns:
            bool: 同期成功可否
        """
        pass
    
    @abstractmethod
    def export_data(self) -> Optional[StandardProjectData]:
        """
        ツールからデータをエクスポート
        
        Returns:
            Optional[StandardProjectData]: エクスポートされたデータ
        """
        pass
    
    @abstractmethod
    def import_data(self, data: StandardProjectData) -> bool:
        """
        ツールにデータをインポート
        
        Args:
            data: インポートするデータ
            
        Returns:
            bool: インポート成功可否
        """
        pass
    
    @abstractmethod
    def get_tool_info(self) -> Dict[str, Any]:
        """
        ツール情報を取得
        
        Returns:
            Dict[str, Any]: ツール情報
        """
        pass
    
    def validate_connection(self) -> bool:
        """
        接続の有効性を検証
        
        Returns:
            bool: 接続が有効かどうか
        """
        return self.is_connected()


class BridgeManager:
    """
    ブリッジマネージャー - 複数のツールアダプターを管理
    """
    
    def __init__(self, project_path: Optional[str] = None):
        self.project_path = Path(project_path or Path.cwd())
        self.adapters: Dict[str, ToolAdapter] = {}
        self.config_path = self.project_path / ".ukf" / "bridge_config.json"
        self._load_config()
    
    def register_adapter(self, adapter: ToolAdapter) -> bool:
        """
        アダプターを登録
        
        Args:
            adapter: 登録するアダプター
            
        Returns:
            bool: 登録成功可否
        """
        try:
            self.adapters[adapter.name] = adapter
            self._save_config()
            return True
        except Exception as e:
            print(f"アダプター登録エラー: {e}")
            return False
    
    def unregister_adapter(self, adapter_name: str) -> bool:
        """
        アダプターの登録を解除
        
        Args:
            adapter_name: アダプター名
            
        Returns:
            bool: 解除成功可否
        """
        try:
            if adapter_name in self.adapters:
                # 接続中の場合は切断
                if self.adapters[adapter_name].is_connected():
                    self.adapters[adapter_name].disconnect()
                del self.adapters[adapter_name]
                self._save_config()
                return True
            return False
        except Exception as e:
            print(f"アダプター登録解除エラー: {e}")
            return False
    
    def connect_adapter(self, adapter_name: str, config: Dict[str, Any]) -> bool:
        """
        特定のアダプターに接続
        
        Args:
            adapter_name: アダプター名
            config: 接続設定
            
        Returns:
            bool: 接続成功可否
        """
        if adapter_name not in self.adapters:
            return False
        
        return self.adapters[adapter_name].connect(config)
    
    def disconnect_adapter(self, adapter_name: str) -> bool:
        """
        特定のアダプターから切断
        
        Args:
            adapter_name: アダプター名
            
        Returns:
            bool: 切断成功可否
        """
        if adapter_name not in self.adapters:
            return False
        
        return self.adapters[adapter_name].disconnect()
    
    def sync_all(self, project_data: StandardProjectData) -> Dict[str, bool]:
        """
        全ての接続済みアダプターでデータ同期
        
        Args:
            project_data: 同期するプロジェクトデータ
            
        Returns:
            Dict[str, bool]: 各アダプターの同期結果
        """
        results = {}
        for name, adapter in self.adapters.items():
            if adapter.is_connected():
                try:
                    results[name] = adapter.sync_data(project_data)
                except Exception as e:
                    print(f"{name} 同期エラー: {e}")
                    results[name] = False
            else:
                results[name] = False
        
        return results
    
    def get_adapter_status(self) -> Dict[str, Dict[str, Any]]:
        """
        全アダプターの状態を取得
        
        Returns:
            Dict[str, Dict[str, Any]]: アダプター状態情報
        """
        status = {}
        for name, adapter in self.adapters.items():
            try:
                status[name] = {
                    "connected": adapter.is_connected(),
                    "info": adapter.get_tool_info(),
                    "last_check": datetime.now().isoformat()
                }
            except Exception as e:
                status[name] = {
                    "connected": False,
                    "error": str(e),
                    "last_check": datetime.now().isoformat()
                }
        
        return status
    
    def list_adapters(self) -> List[str]:
        """
        登録済みアダプター一覧を取得
        
        Returns:
            List[str]: アダプター名のリスト
        """
        return list(self.adapters.keys())
    
    def _load_config(self) -> None:
        """設定ファイルを読み込み"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 設定からアダプターを復元（実装は各アダプタークラスで）
        except Exception as e:
            print(f"設定読み込みエラー: {e}")
    
    def _save_config(self) -> None:
        """設定ファイルに保存"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            config = {
                "adapters": list(self.adapters.keys()),
                "project_path": str(self.project_path),
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"設定保存エラー: {e}")


class StandardDataFormat:
    """
    標準データフォーマット管理クラス
    プロジェクトメタデータの標準化を担当
    """
    
    @staticmethod
    def create_project_data(project_path: Union[str, Path]) -> StandardProjectData:
        """
        プロジェクトパスから標準データを作成
        
        Args:
            project_path: プロジェクトパス
            
        Returns:
            StandardProjectData: 標準プロジェクトデータ
        """
        path = Path(project_path)
        
        # プロジェクト設定読み込み
        config_path = path / ".ukf" / "project.json"
        project_config = {}
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    project_config = json.load(f)
            except Exception:
                pass
        
        # ファイル一覧作成
        files = []
        try:
            for file_path in path.rglob("*"):
                if file_path.is_file() and not any(part.startswith('.') for part in file_path.parts[len(path.parts):]):
                    relative_path = file_path.relative_to(path)
                    files.append({
                        "path": str(relative_path),
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
        except Exception:
            pass
        
        # タスク情報読み込み（もしあれば）
        tasks = []
        task_path = path / ".ukf" / "tasks.json"
        if task_path.exists():
            try:
                with open(task_path, 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
            except Exception:
                pass
        
        return StandardProjectData(
            name=project_config.get('name', path.name),
            description=project_config.get('description', ''),
            path=str(path),
            type=project_config.get('type', 'basic'),
            created_at=project_config.get('created_at', datetime.now().isoformat()),
            last_modified=datetime.now().isoformat(),
            metadata=project_config,
            files=files,
            tasks=tasks,
            tags=project_config.get('tags', [])
        )
    
    @staticmethod
    def validate_data(data: StandardProjectData) -> bool:
        """
        データフォーマットの有効性を検証
        
        Args:
            data: 検証するデータ
            
        Returns:
            bool: データが有効かどうか
        """
        try:
            # 必須フィールドの確認
            required_fields = ['name', 'path', 'type']
            for field in required_fields:
                if not getattr(data, field):
                    return False
            
            # パスの存在確認
            if not Path(data.path).exists():
                return False
            
            return True
        except Exception:
            return False
    
    @staticmethod
    def export_to_json(data: StandardProjectData, output_path: Union[str, Path]) -> bool:
        """
        データをJSONファイルにエクスポート
        
        Args:
            data: エクスポートするデータ
            output_path: 出力パス
            
        Returns:
            bool: エクスポート成功可否
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"JSONエクスポートエラー: {e}")
            return False
    
    @staticmethod
    def import_from_json(input_path: Union[str, Path]) -> Optional[StandardProjectData]:
        """
        JSONファイルからデータをインポート
        
        Args:
            input_path: 入力パス
            
        Returns:
            Optional[StandardProjectData]: インポートされたデータ
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data_dict = json.load(f)
            return StandardProjectData.from_dict(data_dict)
        except Exception as e:
            print(f"JSONインポートエラー: {e}")
            return None