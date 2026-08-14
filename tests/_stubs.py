from __future__ import annotations

import asyncio
import enum
import sys
import types
from types import SimpleNamespace


def install_stubs() -> None:
    if 'FunPayAPI' not in sys.modules:
        funpayapi = types.ModuleType('FunPayAPI')

        class _OrderStatuses(enum.Enum):
            PAID = 'PAID'
            CLOSED = 'CLOSED'
            REFUNDED = 'REFUNDED'

        class _EventTypes(enum.Enum):
            NEW_MESSAGE = 'NEW_MESSAGE'

        class _Enums:
            OrderStatuses = _OrderStatuses
            EventTypes = _EventTypes

        class Account:
            def __init__(self, *args, **kwargs):
                self.id = 12345
                self.requests_timeout = kwargs.get('requests_timeout')

            def get(self, *args, **kwargs):
                return self

            def get_sells(self, *args, **kwargs):
                return (None, [])

            def get_order(self, *args, **kwargs):
                return None

            def get_chat_by_name(self, *args, **kwargs):
                return None

            def send_message(self, *args, **kwargs):
                return True

            def refund(self, *args, **kwargs):
                return True

        class Runner:
            def __init__(self, account):
                self.account = account

            def listen(self, requests_delay=2):
                if False:
                    yield None
                return iter(())

        funpayapi.Account = Account
        funpayapi.Runner = Runner
        funpayapi.enums = _Enums
        sys.modules['FunPayAPI'] = funpayapi

    if 'aiogram' not in sys.modules:
        aiogram = types.ModuleType('aiogram')

        class _DummySession:
            closed = False

            async def close(self):
                self.closed = True

        class Bot:
            def __init__(self, token: str):
                self.token = token
                self.session = _DummySession()

            async def get_me(self):
                return SimpleNamespace(id=1, username='stub_bot')

            async def send_message(self, *args, **kwargs):
                return True

        class Dispatcher:
            def __init__(self, storage=None):
                self.storage = storage

            def message(self, *args, **kwargs):
                def decorator(func):
                    return func
                return decorator

            async def start_polling(self, *args, **kwargs):
                return None

            async def stop_polling(self):
                return None

        class Message:
            pass

        aiogram.Bot = Bot
        aiogram.Dispatcher = Dispatcher
        aiogram.types = SimpleNamespace(Message=Message)
        filters = types.ModuleType('aiogram.filters')

        class Command:
            def __init__(self, *args, **kwargs):
                self.args = args

        filters.Command = Command
        sys.modules['aiogram'] = aiogram
        sys.modules['aiogram.filters'] = filters
        fsm = types.ModuleType('aiogram.fsm')
        storage = types.ModuleType('aiogram.fsm.storage')
        memory = types.ModuleType('aiogram.fsm.storage.memory')

        class MemoryStorage:
            pass

        memory.MemoryStorage = MemoryStorage
        sys.modules['aiogram.fsm'] = fsm
        sys.modules['aiogram.fsm.storage'] = storage
        sys.modules['aiogram.fsm.storage.memory'] = memory

    if 'tonutils' not in sys.modules:
        tonutils = types.ModuleType('tonutils')
        client = types.ModuleType('tonutils.client')
        wallet_mod = types.ModuleType('tonutils.wallet')

        class _StubAddress:
            def __init__(self, address: str = '0:' + 'a' * 64):
                self._address = address

            def to_str(self, *args, **kwargs):
                return self._address

        class _StubPublicKey:
            as_hex = "ab" * 32

        class _StubStateInit:
            def serialize(self):
                return self

            def to_boc(self):
                return b"stub-state-init"

        class _StubWallet:
            def __init__(self):
                self.address = _StubAddress()
                self.state_init = _StubStateInit()

            async def balance(self):
                return 1_000_000_000

            async def transfer(self, destination, amount, body):
                return 'stub_tx_hash'

        class TonapiClient:
            def __init__(self, api_key=None, is_testnet=False):
                self.api_key = api_key
                self.is_testnet = is_testnet

        class WalletV4R2:
            @classmethod
            def from_mnemonic(cls, client, mnemonic):
                return _StubWallet(), _StubPublicKey(), None, mnemonic

        client.TonapiClient = TonapiClient
        wallet_mod.WalletV4R2 = WalletV4R2
        sys.modules['tonutils'] = tonutils
        sys.modules['tonutils.client'] = client
        sys.modules['tonutils.wallet'] = wallet_mod
