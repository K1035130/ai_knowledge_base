interface BubbleConfig {
  left?: string;
  right?: string;
  size: number;
  gradient: string;
  duration: number;
  delay: number;
}

const BUBBLES: BubbleConfig[] = [
  { left: "1%", size: 170, gradient: "linear-gradient(135deg, #fde68a, #4ade80)", duration: 22, delay: -2 },
  { right: "3%", size: 130, gradient: "linear-gradient(135deg, #4ade80, #38bdf8)", duration: 27, delay: -10 },
  { left: "9%", size: 95, gradient: "linear-gradient(135deg, #38bdf8, #a78bfa)", duration: 18, delay: -6 },
  { right: "9%", size: 210, gradient: "linear-gradient(135deg, #fde68a, #38bdf8)", duration: 31, delay: -16 },
  { left: "-5%", size: 250, gradient: "linear-gradient(135deg, #4ade80, #fde68a)", duration: 35, delay: -4 },
  { right: "-7%", size: 190, gradient: "linear-gradient(135deg, #a78bfa, #4ade80)", duration: 25, delay: -20 },
  { left: "4%", size: 60, gradient: "linear-gradient(135deg, #38bdf8, #fde68a)", duration: 16, delay: -8 },
  { left: "20%", size: 80, gradient: "linear-gradient(135deg, #fde68a, #a78bfa)", duration: 20, delay: -14 },
  { right: "22%", size: 110, gradient: "linear-gradient(135deg, #4ade80, #38bdf8)", duration: 29, delay: -3 },
  { left: "15%", size: 150, gradient: "linear-gradient(135deg, #38bdf8, #4ade80)", duration: 24, delay: -18 },
  { right: "16%", size: 70, gradient: "linear-gradient(135deg, #a78bfa, #fde68a)", duration: 17, delay: -11 },
  { left: "-2%", size: 120, gradient: "linear-gradient(135deg, #fde68a, #38bdf8)", duration: 28, delay: -7 },
  { right: "-1%", size: 160, gradient: "linear-gradient(135deg, #4ade80, #a78bfa)", duration: 23, delay: -22 },
  { left: "30%", size: 55, gradient: "linear-gradient(135deg, #38bdf8, #fde68a)", duration: 15, delay: -5 },
  { right: "30%", size: 90, gradient: "linear-gradient(135deg, #a78bfa, #4ade80)", duration: 21, delay: -13 },
];

export default function BackgroundBubbles() {
  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
      {BUBBLES.map((bubble, i) => (
        <div
          key={i}
          className="bubble"
          style={{
            left: bubble.left,
            right: bubble.right,
            bottom: "-25%",
            width: bubble.size,
            height: bubble.size,
            background: bubble.gradient,
            animationDuration: `${bubble.duration}s`,
            animationDelay: `${bubble.delay}s`,
          }}
        />
      ))}
    </div>
  );
}
