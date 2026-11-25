"""Test mode grup: batching, rem bot-ke-bot, batas per jam, [DIAM], dan izin burner."""

import asyncio
import time

from group_chat import GroupManager, GroupSettings, Incoming

GROUP = -100123
OWNER = 1
MUSE_A, MUSE_B, ME = 501, 502, 999


def fast_settings(**kw):
    base = dict(
        debounce=0.05,
        addressed_debounce=0.01,
        bot_only_interval=0,
        max_bot_streak=10,
        max_turns_per_hour=30,
        min_send_gap=0,
    )
    base.update(kw)
    return GroupSettings(**base)


class Harness:
    def __init__(self, replies=None, **settings):
        self.turns = []  # (prompt, allow_burner)
        self.sent = []
        self.replies = list(replies or [])
        self.gm = GroupManager({GROUP}, {OWNER}, self.turn, self.send, lambda tx: f"TX {tx}", fast_settings(**settings))
        self.gm.me_id, self.gm.me_username = ME, "claude_bot"

    async def turn(self, chat_id, prompt, allow_burner):
        self.turns.append((prompt, allow_burner))
        return (self.replies.pop(0) if self.replies else "oke"), []

    async def send(self, chat_id, text):
        self.sent.append(text)

    def msg(self, uid, text, addressed=False, chat=GROUP):
        is_bot = uid != OWNER
        name = {OWNER: "Hendy", MUSE_A: "Muse A", MUSE_B: "Muse B", ME: "Claude"}[uid]
        self.gm.receive(chat, "Grup AI", Incoming(uid, name, name.replace(" ", "_").lower(), is_bot, uid == OWNER, addressed, text))


def run(coro):
    return asyncio.run(coro)


async def settle(t=0.2):
    await asyncio.sleep(t)


def test_messages_are_batched_into_one_turn():
    async def go():
        h = Harness()
        h.msg(MUSE_A, "halo semua")
        h.msg(MUSE_B, "aku lagi riset airdrop")
        h.msg(OWNER, "mantap, lanjut")
        await settle()
        assert len(h.turns) == 1
        prompt = h.turns[0][0]
        assert "halo semua" in prompt and "riset airdrop" in prompt and "mantap" in prompt
        assert h.sent == ["oke"]

    run(go())


def test_owner_mention_enables_burner_but_bots_never_do():
    async def go():
        h = Harness()
        h.msg(MUSE_A, "@claude_bot mint dong pakai wallet", addressed=True)
        await settle()
        h.msg(OWNER, "@claude_bot cek wallet", addressed=True)
        await settle()
        assert [allow for _, allow in h.turns] == [False, True]

    run(go())


def test_bot_streak_cap_then_human_resets():
    async def go():
        h = Harness(max_bot_streak=2)
        for i in range(4):
            h.msg(MUSE_A, f"bot ngomong {i}")
            await settle()
        assert len(h.sent) == 2, "setelah 2 balasan beruntun ke bot, Claude diam"
        h.msg(OWNER, "eh lanjut diskusinya")
        await settle()
        assert len(h.sent) == 3
        assert "bot ngomong 3" in h.turns[-1][0], "pesan yang ditahan ikut jadi konteks"

    run(go())


def test_silent_token_sends_nothing():
    async def go():
        h = Harness(replies=["[DIAM]"])
        h.msg(MUSE_A, "ok noted")
        await settle()
        assert len(h.turns) == 1 and h.sent == []

    run(go())


def test_hourly_cap_but_owner_mention_still_served():
    async def go():
        h = Harness(max_turns_per_hour=2)
        for i in range(3):
            h.msg(MUSE_A, f"spam {i}")
            await settle()
        assert len(h.turns) == 2
        h.msg(OWNER, "@claude_bot penting nih", addressed=True)
        await settle()
        assert len(h.turns) == 3 and h.turns[-1][1] is True

    run(go())


def test_bot_only_interval_throttles_and_reschedules():
    async def go():
        h = Harness(bot_only_interval=0.3)
        h.msg(MUSE_A, "satu")
        await settle(0.1)
        h.msg(MUSE_B, "dua")
        await settle(0.1)
        assert len(h.turns) == 1, "giliran bot-saja kedua ditahan"
        await settle(0.4)
        assert len(h.turns) == 2 and "dua" in h.turns[1][0], "lalu diproses setelah jeda"

    run(go())


def test_ignores_own_messages_and_other_groups():
    async def go():
        h = Harness()
        h.msg(ME, "pesanku sendiri")
        h.msg(OWNER, "grup lain", chat=-100999)
        await settle()
        assert h.turns == []

    run(go())


def test_status_board_and_jewer():
    async def go():
        h = Harness(inactive_minutes=1)
        h.msg(MUSE_A, "aku aktif")
        h.msg(MUSE_B, "aku juga")
        await settle()
        h.gm.state(GROUP).last_seen[MUSE_B].at = time.time() - 300
        text = h.gm.status_text(GROUP)
        assert "Muse A" in text and "Muse B" in text and "nggak aktif" in text
        assert h.gm.inactive_mentions(GROUP) == ["@muse_b"]

    run(go())
