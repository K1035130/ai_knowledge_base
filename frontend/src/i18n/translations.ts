export type Lang = "zh" | "en";

export const translations = {
  zh: {
    title: "AI 使用年度报告",
    dropzone: {
      active: "松手上传",
      idle: "拖拽你的 ChatGPT 导出文件到这里",
      hint: "支持多个 conversations.json，点击也可以选择文件",
    },
    guide: {
      heading: "如何获取你的 ChatGPT 导出文件",
      steps: [
        { title: "打开设置", desc: "登录 ChatGPT 网页版，点击左下角头像，进入 Settings" },
        { title: "数据控制", desc: "在设置里找到 Data controls（数据控制）" },
        { title: "导出数据", desc: "点击 Export data，确认导出请求" },
        { title: "查收邮件", desc: "几分钟后注册邮箱会收到一封邮件，下载里面的 zip 文件" },
        { title: "拖入上传", desc: "解压后找到 conversations.json，拖到上面的框里即可" },
      ],
    },
    privacy: {
      heading: "使用前请注意",
      body: "请确认你上传的对话文件中不包含密码、身份证号等敏感隐私信息。\n\n我们承诺：不会保存你的对话数据，也不会将其用于生成本报告之外的任何用途。",
      ack: "我已了解",
    },
    processing: "处理中...",
    processingHint: "这可能需要三到五分钟",
    errorPrefix: "出错了：",
    retry: "重试",
    reupload: "上传新的导出文件",
    sections: {
      overview: "总览",
      activity: "什么时候在用 AI",
      topics: "最长讨论的话题",
      highlights: "你或许对这些话题仍有印象",
      habits: "使用习惯",
      ending: "就是这些啦",
    },
    nav: {
      prev: "上一页",
      next: "下一页",
    },
    export: {
      button: "导出 HTML",
      generating: "正在生成…",
      error: "导出失败，请重试",
    },
    overview: {
      total_conversations: "对话总数",
      total_messages: "消息总数",
      active_days: "活跃天数",
      avg_session: "平均单次会话",
      longest_session: "最长单次会话",
      avg_thread_span: "平均对话线程跨度",
      avg_response: "平均响应时间",
      minutes: "分钟",
      hours: "小时",
      seconds: "秒",
    },
    charts: {
      byHour: "一天中的活跃时段",
      byWeekday: "一周中的活跃分布",
      byMonth: "月度使用趋势",
      weekdays: ["一", "二", "三", "四", "五", "六", "日"],
    },
    rewrite: {
      heading: "重写 / 重新生成",
      summary: (pct: number, edited: number, total: number) =>
        `${pct}% 的对话里你改写过问题或让 AI 重新生成（${edited}/${total}）`,
      detail: (userEdits: number, regens: number) => `用户改写 ${userEdits} 次，AI 重新生成 ${regens} 次`,
    },
    language: {
      heading: "语言占比",
      labels: { "zh-cn": "中文", en: "英文", other: "其他" } as Record<string, string>,
    },
  },
  en: {
    title: "AI Usage Annual Report",
    dropzone: {
      active: "Drop to upload",
      idle: "Drag your ChatGPT export here",
      hint: "Supports multiple conversations.json files — click to browse",
    },
    guide: {
      heading: "How to get your ChatGPT export file",
      steps: [
        { title: "Open Settings", desc: "Log into ChatGPT on the web, click your avatar, then Settings" },
        { title: "Data controls", desc: "Find Data controls in the settings menu" },
        { title: "Export data", desc: "Click Export data and confirm the request" },
        { title: "Check your email", desc: "A few minutes later you'll get an email — download the zip file" },
        { title: "Drop it above", desc: "Unzip it, find conversations.json, and drop it into the box above" },
      ],
    },
    privacy: {
      heading: "Before you upload",
      body: "Please make sure your conversation file doesn't contain passwords, ID numbers, or other sensitive personal information.\n\nOur promise: we never store your conversation data, and we never use it for anything beyond generating this report.",
      ack: "Got it",
    },
    processing: "Processing...",
    processingHint: "This might take three to five minutes",
    errorPrefix: "Something went wrong: ",
    retry: "Retry",
    reupload: "Upload a new export",
    sections: {
      overview: "Overview",
      activity: "When you use AI",
      topics: "The topics you discussed most",
      highlights: "You might still remember these",
      habits: "Habits",
      ending: "That's a wrap",
    },
    nav: {
      prev: "Previous",
      next: "Next",
    },
    export: {
      button: "Export HTML",
      generating: "Generating…",
      error: "Export failed, please try again",
    },
    overview: {
      total_conversations: "Total conversations",
      total_messages: "Total messages",
      active_days: "Active days",
      avg_session: "Avg. session",
      longest_session: "Longest session",
      avg_thread_span: "Avg. thread span",
      avg_response: "Avg. response time",
      minutes: "min",
      hours: "hr",
      seconds: "sec",
    },
    charts: {
      byHour: "Activity by hour",
      byWeekday: "Activity by weekday",
      byMonth: "Monthly trend",
      weekdays: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    },
    rewrite: {
      heading: "Edits / regenerations",
      summary: (pct: number, edited: number, total: number) =>
        `You edited a question or regenerated a reply in ${pct}% of conversations (${edited}/${total})`,
      detail: (userEdits: number, regens: number) => `You edited ${userEdits} times, AI regenerated ${regens} times`,
    },
    language: {
      heading: "Language mix",
      labels: { "zh-cn": "Chinese", en: "English", other: "Other" } as Record<string, string>,
    },
  },
} satisfies Record<Lang, unknown>;
