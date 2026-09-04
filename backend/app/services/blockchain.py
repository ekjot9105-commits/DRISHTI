import hashlib
import json
import time
import os
import threading
from typing import Dict, Any, List
import queue

class Block:
    def __init__(self, index: int, timestamp: float, event_id: int, evidence_hash: str, event_hash: str, previous_hash: str):
        self.index = index
        self.timestamp = timestamp
        self.event_id = event_id
        self.evidence_hash = evidence_hash
        self.event_hash = event_hash
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = ""

    def calculate_hash(self) -> str:
        block_string = f"{self.index}{self.timestamp}{self.event_id}{self.evidence_hash}{self.event_hash}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def mine_block(self, difficulty: int = 3):
        target = "0" * difficulty
        self.hash = self.calculate_hash()
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "event_id": self.event_id,
            "evidence_hash": self.evidence_hash,
            "event_hash": self.event_hash,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash
        }

    @staticmethod
    def from_dict(data: dict) -> 'Block':
        block = Block(
            data["index"],
            data["timestamp"],
            data["event_id"],
            data["evidence_hash"],
            data["event_hash"],
            data["previous_hash"]
        )
        block.nonce = data["nonce"]
        block.hash = data["hash"]
        return block


class BlockchainService:
    def __init__(self, storage_path: str = "data/blockchain/ledger.json", difficulty: int = 3):
        self.chain: List[Block] = []
        self.storage_path = storage_path
        self.difficulty = difficulty
        self.lock = threading.Lock()
        
        # Async mining queue to avoid blocking
        self.mining_queue = queue.Queue()
        self.mining_thread = threading.Thread(target=self._mining_worker, daemon=True)
        
        self.load_chain()
        self.mining_thread.start()

    def _mining_worker(self):
        while True:
            try:
                task = self.mining_queue.get()
                if task is None:
                    break
                event_id, evidence_hash, event_hash = task
                self._add_block(event_id, evidence_hash, event_hash)
            except Exception as e:
                print(f"[Blockchain] Mining error: {e}")

    def load_chain(self):
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r") as f:
                try:
                    data = json.load(f)
                    self.chain = [Block.from_dict(b) for b in data]
                    return
                except:
                    pass
        
        # Create Genesis Block
        self._add_block(0, "genesis_evidence", "genesis_event")

    def save_chain(self):
        with open(self.storage_path, "w") as f:
            json.dump([b.to_dict() for b in self.chain], f, indent=4)

    def get_latest_block(self) -> Block:
        return self.chain[-1]

    def _add_block(self, event_id: int, evidence_hash: str, event_hash: str):
        with self.lock:
            latest = self.get_latest_block() if self.chain else None
            idx = latest.index + 1 if latest else 0
            prev_hash = latest.hash if latest else "0" * 64
            
            new_block = Block(
                index=idx,
                timestamp=time.time(),
                event_id=event_id,
                evidence_hash=evidence_hash,
                event_hash=event_hash,
                previous_hash=prev_hash
            )
            
            # Mine (this blocks the thread, but we are running in a dedicated mining_worker)
            new_block.mine_block(self.difficulty)
            
            self.chain.append(new_block)
            self.save_chain()
            return new_block

    def queue_transaction(self, event_id: int, evidence_hash: str, event_hash: str):
        """Non-blocking function to add a transaction to the mining queue."""
        self.mining_queue.put((event_id, evidence_hash, event_hash))

    def get_block_by_event(self, event_id: int) -> dict:
        for block in reversed(self.chain):
            if block.event_id == event_id:
                return block.to_dict()
        return None

    def verify_chain(self) -> bool:
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            prev = self.chain[i - 1]
            if current.hash != current.calculate_hash():
                return False
            if current.previous_hash != prev.hash:
                return False
        return True

# Singleton instance
blockchain_service = BlockchainService()
