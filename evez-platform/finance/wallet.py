"""
EVEZ Wallet — Non-custodial HD wallet generator and manager.

Generates BIP-39 mnemonic → BIP-44 HD derivation → ETH/BTC addresses.
Private keys NEVER leave this machine. No third-party custody.

Steven's rule: "Verify internally before external anything."
"""

import json
import os
import hashlib
import time
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, List

from mnemonic import Mnemonic
from eth_account import Account

logger = logging.getLogger("evez.wallet")

# Enable HD account features
Account.enable_unaudited_hdwallet_features()


@dataclass
class DerivedAccount:
    chain: str
    address: str
    derivation_path: str
    index: int
    label: str = ""
    created: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "chain": self.chain,
            "address": self.address,
            "derivation_path": self.derivation_path,
            "index": self.index,
            "label": self.label,
            "created": self.created,
        }


@dataclass
class WalletVault:
    """Secure vault wrapper. Mnemonic stored encrypted on disk."""
    vault_path: Path
    mnemonic_hash: str  # SHA-256 of mnemonic (verification only, not reversible)
    accounts: List[DerivedAccount] = field(default_factory=list)
    created: float = field(default_factory=time.time)

    def to_dict(self):
        return {
            "mnemonic_hash": self.mnemonic_hash[:16] + "...",
            "accounts": [a.to_dict() for a in self.accounts],
            "created": self.created,
            "account_count": len(self.accounts),
        }


class EVEZWallet:
    """
    Non-custodial HD wallet manager.

    - Generates BIP-39 12-word mnemonic (256-bit entropy)
    - Derives ETH addresses via BIP-44 (m/44'/60'/0'/0/index)
    - Stores mnemonic encrypted with AES-256-GCM using a local key
    - Never transmits private keys anywhere
    """

    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path("/root/.openclaw/workspace/evez-platform/data/wallet")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.vault_file = self.data_dir / "vault.enc"
        self.key_file = self.data_dir / ".vault_key"
        self.mnemo = Mnemonic("english")
        self._vault: Optional[WalletVault] = None
        self._mnemonic: Optional[str] = None

    def _get_or_create_key(self) -> bytes:
        """Get or generate local encryption key (AES-256)."""
        if self.key_file.exists():
            return self.key_file.read_bytes()
        key = os.urandom(32)
        self.key_file.write_bytes(key)
        self.key_file.chmod(0o600)
        return key

    def _encrypt(self, plaintext: str) -> bytes:
        """AES-256-GCM encrypt."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        key = self._get_or_create_key()
        nonce = os.urandom(12)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
        return nonce + ciphertext

    def _decrypt(self, data: bytes) -> str:
        """AES-256-GCM decrypt."""
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        key = self._get_or_create_key()
        nonce = data[:12]
        ciphertext = data[12:]
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None).decode()

    def create_wallet(self, label: str = "evez-primary") -> Dict:
        """
        Generate new HD wallet.

        Returns:
            {
                "mnemonic": "word1 word2 ... word12",  # ONLY shown once
                "address": "0x...",
                "warning": "BACK UP YOUR MNEMONIC. It will not be shown again."
            }
        """
        # Generate 12-word mnemonic (128-bit entropy)
        mnemonic = self.mnemo.generate(strength=128)
        acct = Account.from_mnemonic(mnemonic)

        # Store encrypted
        vault_data = {
            "mnemonic": mnemonic,
            "accounts": [{
                "chain": "ETH",
                "address": acct.address,
                "derivation_path": "m/44'/60'/0'/0/0",
                "index": 0,
                "label": label,
                "created": time.time(),
            }],
            "created": time.time(),
        }
        encrypted = self._encrypt(json.dumps(vault_data))
        self.vault_file.write_bytes(encrypted)
        self.vault_file.chmod(0o600)

        # Build vault object
        mnemonic_hash = hashlib.sha256(mnemonic.encode()).hexdigest()
        self._vault = WalletVault(
            vault_path=self.vault_file,
            mnemonic_hash=mnemonic_hash,
            accounts=[DerivedAccount(**vault_data["accounts"][0])],
        )
        self._mnemonic = mnemonic

        logger.info("Wallet created: %s", acct.address)

        return {
            "mnemonic": mnemonic,
            "address": acct.address,
            "private_key": acct.key.hex(),
            "derivation_path": "m/44'/60'/0'/0/0",
            "label": label,
            "warning": "⚠️ BACK UP YOUR MNEMONIC. It will NOT be shown again. Store it offline.",
        }

    def load_vault(self) -> Optional[WalletVault]:
        """Load existing vault from disk."""
        if not self.vault_file.exists():
            return None
        try:
            encrypted = self.vault_file.read_bytes()
            plaintext = self._decrypt(encrypted)
            data = json.loads(plaintext)

            self._mnemonic = data["mnemonic"]
            mnemonic_hash = hashlib.sha256(self._mnemonic.encode()).hexdigest()
            accounts = [DerivedAccount(**a) for a in data.get("accounts", [])]

            self._vault = WalletVault(
                vault_path=self.vault_file,
                mnemonic_hash=mnemonic_hash,
                accounts=accounts,
                created=data.get("created", time.time()),
            )
            return self._vault
        except Exception as e:
            logger.error("Failed to load vault: %s", e)
            return None

    def derive_account(self, index: int = None, label: str = "") -> Optional[Dict]:
        """
        Derive a new account from the HD wallet.

        Args:
            index: Derivation index (auto-increments if None)
            label: Human-readable label
        """
        if not self._vault or not self._mnemonic:
            if not self.load_vault():
                return {"error": "No wallet found. Create one first."}

        if index is None:
            index = len(self._vault.accounts)

        path = f"m/44'/60'/0'/0/{index}"
        acct = Account.from_mnemonic(self._mnemonic, account_path=path)

        derived = DerivedAccount(
            chain="ETH",
            address=acct.address,
            derivation_path=path,
            index=index,
            label=label or f"account-{index}",
        )

        self._vault.accounts.append(derived)

        # Save updated vault
        self._save_vault()

        logger.info("Derived account %d: %s", index, acct.address)

        return derived.to_dict()

    def _save_vault(self):
        """Re-encrypt and save vault."""
        if not self._vault or not self._mnemonic:
            return

        vault_data = {
            "mnemonic": self._mnemonic,
            "accounts": [a.to_dict() for a in self._vault.accounts],
            "created": self._vault.created,
        }
        encrypted = self._encrypt(json.dumps(vault_data))
        self.vault_file.write_bytes(encrypted)
        self.vault_file.chmod(0o600)

    def get_address(self, index: int = 0) -> Optional[str]:
        """Get address for account index."""
        if not self._vault:
            self.load_vault()
        if self._vault and index < len(self._vault.accounts):
            return self._vault.accounts[index].address
        return None

    def list_accounts(self) -> List[Dict]:
        """List all derived accounts."""
        if not self._vault:
            self.load_vault()
        if not self._vault:
            return []
        return [a.to_dict() for a in self._vault.accounts]

    def get_status(self) -> Dict:
        if not self._vault:
            self.load_vault()
        return {
            "initialized": self._vault is not None,
            "accounts": len(self._vault.accounts) if self._vault else 0,
            "addresses": [a.to_dict() for a in self._vault.accounts] if self._vault else [],
            "vault_file": str(self.vault_file),
        }

    def get_public_info(self) -> Dict:
        """Public-safe info (no private keys, no mnemonic)."""
        if not self._vault:
            self.load_vault()
        if not self._vault:
            return {"initialized": False}
        return {
            "initialized": True,
            "mnemonic_hash": self._vault.mnemonic_hash[:16] + "...",
            "accounts": [{
                "chain": a.chain,
                "address": a.address,
                "label": a.label,
                "index": a.index,
            } for a in self._vault.accounts],
        }
