"""A 4 KB chess engine for make.fun's tiny-chess-01.

It plays each game through the env at MAKEFUN_ENV_URL: POST /game {} serves
the position in play, POST /move {game, move} plays your move, and the loop
ends when the env answers status "done".

The chess is one ply deep for now: of the legal moves the env lists, it plays
the one that captures the most valuable piece. The next commit replaces that
with a search under a fixed depth budget. No clock and no random, so a
replay of a trial gives the same moves.
"""

import json
import os
import sys
import urllib.error
import urllib.request

ENV_URL = os.environ.get("MAKEFUN_ENV_URL") or sys.exit("MAKEFUN_ENV_URL is not set")

# Piece values by FEN letter, case-insensitive.
VALUE = {"p": 1, "n": 3, "b": 3, "r": 5, "q": 9, "k": 100}


def post(path, body):
    """POST a JSON body to the env and return its JSON answer."""
    request = urllib.request.Request(
        ENV_URL + path,
        data=json.dumps(body).encode(),
        headers={"content-type": "application/json"},
    )
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def board_of(fen):
    """The FEN's pieces as {square: letter}, e.g. {"e1": "K", "e8": "k"}."""
    board = {}
    for row, rank in enumerate(fen.split()[0].split("/")):
        file = 0
        for cell in rank:
            if cell.isdigit():
                file += int(cell)
            else:
                board["abcdefgh"[file] + str(8 - row)] = cell
                file += 1
    return board


def choose(fen, legal):
    """The legal UCI move that takes the most, with a fixed tie-break."""
    board = board_of(fen)

    def rank(move):
        mover = board[move[:2]].lower()
        victim = board.get(move[2:4])
        taken = VALUE[victim.lower()] if victim else 0
        promotion = VALUE[move[4]] if len(move) == 5 else 0
        return (-taken, -promotion, VALUE[mover], move)

    return min(legal, key=rank)


def main():
    while True:
        state = post("/game", {})
        if state["status"] == "done":
            break
        while state["status"] == "your_move":
            state = post("/move", {"game": state["game"], "move": choose(state["fen"], state["legal_moves"])})


if __name__ == "__main__":
    main()
