import { useState, useEffect, useCallback, useRef } from "react";

type Grid = number[][];

const SIZE = 4;

function createEmptyGrid(): Grid {
  return Array.from({ length: SIZE }, () => Array(SIZE).fill(0));
}

function addRandomTile(grid: Grid): Grid {
  const empty: [number, number][] = [];
  for (let r = 0; r < SIZE; r++)
    for (let c = 0; c < SIZE; c++)
      if (grid[r][c] === 0) empty.push([r, c]);
  if (empty.length === 0) return grid;
  const [r, c] = empty[Math.floor(Math.random() * empty.length)];
  const next = grid.map((row) => [...row]);
  next[r][c] = Math.random() < 0.9 ? 2 : 4;
  return next;
}

function slideLeft(row: number[]): { row: number[]; score: number } {
  const filtered = row.filter((v) => v !== 0);
  const merged: number[] = [];
  let score = 0;
  let i = 0;
  while (i < filtered.length) {
    if (i + 1 < filtered.length && filtered[i] === filtered[i + 1]) {
      const val = filtered[i] * 2;
      merged.push(val);
      score += val;
      i += 2;
    } else {
      merged.push(filtered[i]);
      i++;
    }
  }
  while (merged.length < SIZE) merged.push(0);
  return { row: merged, score };
}

function rotateClockwise(grid: Grid): Grid {
  return Array.from({ length: SIZE }, (_, r) =>
    Array.from({ length: SIZE }, (_, c) => grid[SIZE - 1 - c][r]),
  );
}

function applyMove(
  grid: Grid,
  direction: "left" | "right" | "up" | "down",
): { grid: Grid; score: number; moved: boolean } {
  let g = grid;
  if (direction === "right") g = rotateClockwise(rotateClockwise(g));
  if (direction === "up") g = rotateClockwise(rotateClockwise(rotateClockwise(g)));
  if (direction === "down") g = rotateClockwise(g);

  let totalScore = 0;
  let moved = false;
  const slid = g.map((row) => {
    const { row: newRow, score } = slideLeft(row);
    totalScore += score;
    if (newRow.some((v, i) => v !== row[i])) moved = true;
    return newRow;
  });

  let result = slid;
  if (direction === "right") result = rotateClockwise(rotateClockwise(slid));
  if (direction === "up") result = rotateClockwise(slid);
  if (direction === "down") result = rotateClockwise(rotateClockwise(rotateClockwise(slid)));
  return { grid: result, score: totalScore, moved };
}

function hasMovesLeft(grid: Grid): boolean {
  for (let r = 0; r < SIZE; r++)
    for (let c = 0; c < SIZE; c++) {
      if (grid[r][c] === 0) return true;
      if (c + 1 < SIZE && grid[r][c] === grid[r][c + 1]) return true;
      if (r + 1 < SIZE && grid[r][c] === grid[r + 1][c]) return true;
    }
  return false;
}

const TILE_CLASSES: Record<number, string> = {
  0: "bg-white/5",
  2: "bg-white/15 text-white/80",
  4: "bg-white/22 text-white/90",
  8: "bg-violet-500/50 text-white",
  16: "bg-violet-500/75 text-white",
  32: "bg-violet-600/85 text-white",
  64: "bg-violet-700 text-white",
  128: "bg-fuchsia-500/80 text-white",
  256: "bg-fuchsia-600 text-white",
  512: "bg-pink-500/80 text-white",
  1024: "bg-pink-600 text-white",
  2048: "bg-amber-400 text-[#1a1430]",
};

function tileClasses(value: number): string {
  return TILE_CLASSES[value] ?? "bg-amber-300 text-[#1a1430]";
}

function tileTextSize(value: number): string {
  if (value >= 1000) return "text-base";
  if (value >= 100) return "text-lg";
  return "text-xl";
}

interface Props {
  reportReady: boolean;
  step: string;
  onViewReport: () => void;
}

export default function Game2048({ reportReady, step, onViewReport }: Props) {
  const [grid, setGrid] = useState<Grid>(() =>
    addRandomTile(addRandomTile(createEmptyGrid())),
  );
  const [score, setScore] = useState(0);
  const [gameOver, setGameOver] = useState(false);
  const touchStart = useRef<{ x: number; y: number } | null>(null);

  const handleMove = useCallback((direction: "left" | "right" | "up" | "down") => {
    setGrid((prev) => {
      const { grid: next, score: gained, moved } = applyMove(prev, direction);
      if (!moved) return prev;
      setScore((s) => s + gained);
      const withTile = addRandomTile(next);
      if (!hasMovesLeft(withTile)) setGameOver(true);
      return withTile;
    });
  }, []);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (gameOver) return;
      const map: Record<string, "left" | "right" | "up" | "down"> = {
        ArrowLeft: "left",
        ArrowRight: "right",
        ArrowUp: "up",
        ArrowDown: "down",
      };
      const dir = map[e.key];
      if (dir) {
        e.preventDefault();
        handleMove(dir);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [gameOver, handleMove]);

  function restart() {
    setGrid(addRandomTile(addRandomTile(createEmptyGrid())));
    setScore(0);
    setGameOver(false);
  }

  function onTouchStart(e: React.TouchEvent) {
    const t = e.touches[0];
    touchStart.current = { x: t.clientX, y: t.clientY };
  }

  function onTouchEnd(e: React.TouchEvent) {
    if (!touchStart.current || gameOver) return;
    const dx = e.changedTouches[0].clientX - touchStart.current.x;
    const dy = e.changedTouches[0].clientY - touchStart.current.y;
    touchStart.current = null;
    if (Math.abs(dx) < 20 && Math.abs(dy) < 20) return;
    if (Math.abs(dx) > Math.abs(dy)) handleMove(dx > 0 ? "right" : "left");
    else handleMove(dy > 0 ? "down" : "up");
  }

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="flex items-center gap-6">
        <div className="text-center">
          <p className="text-xs uppercase tracking-wider text-white/40">Score</p>
          <p className="text-2xl font-bold text-white">{score}</p>
        </div>
        <button
          onClick={restart}
          className="rounded-lg bg-white/10 px-3 py-1.5 text-sm text-white/70 hover:bg-white/20"
        >
          New game
        </button>
      </div>

      <div
        className="relative grid grid-cols-4 gap-2 rounded-2xl bg-white/5 p-3 touch-none"
        onTouchStart={onTouchStart}
        onTouchEnd={onTouchEnd}
      >
        {grid.flat().map((value, i) => (
          <div
            key={i}
            className={`flex h-16 w-16 items-center justify-center rounded-xl font-bold transition-all ${tileClasses(value)} ${tileTextSize(value)}`}
          >
            {value !== 0 ? value : ""}
          </div>
        ))}

        {gameOver && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 rounded-2xl bg-black/60 backdrop-blur-sm">
            <p className="text-xl font-bold text-white">Game Over</p>
            <button
              onClick={restart}
              className="rounded-lg bg-violet-500 px-4 py-2 text-sm text-white hover:bg-violet-400"
            >
              Try again
            </button>
          </div>
        )}
      </div>

      <p className="text-xs text-white/40">
        ← → ↑ ↓ 方向键控制 · Use arrow keys to play
      </p>

      {!reportReady && (
        <p className="text-xs text-white/30">{step || "Processing…"}</p>
      )}

      {reportReady && (
        <button
          onClick={onViewReport}
          className="mt-2 animate-pulse rounded-xl bg-violet-500 px-6 py-3 text-base font-semibold text-white shadow-lg shadow-violet-500/30 hover:animate-none hover:bg-violet-400"
        >
          报告已生成，点击查看 →
        </button>
      )}
    </div>
  );
}
