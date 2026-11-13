export const metadata = { title: "How this works" };

export default function About() {
  return (
    <article className="space-y-4 max-w-prose">
      <h1 className="text-2xl font-semibold">How this works</h1>
      <ol className="list-decimal pl-5 space-y-2">
        <li><strong>Read the records.</strong> Code reads each item&apos;s official page and staff report: the steps, dates, results and votes. No AI is used for these facts.</li>
        <li><strong>Draft.</strong> An AI model drafts short plain-language sentences. Each one must quote the exact words it comes from and say which step it is from.</li>
        <li><strong>Check.</strong> Code rejects any sentence whose quote is not in the source, and flags dates, deadlines, decision words used for recommendations, and loaded words. A second AI pass checks each sentence against its source.</li>
        <li><strong>Review.</strong> A person approves, edits or rejects every sentence. Only approved sentences are shown.</li>
        <li><strong>Watch for changes.</strong> If the official record changes, the card is marked until it is checked again.</li>
      </ol>
      <h2 className="text-xl font-semibold">What we never do</h2>
      <ul className="list-disc pl-5 space-y-1">
        <li>Guess a comment deadline. We show one only if the City&apos;s page states it.</li>
        <li>Summarize or name members of the public who wrote in. We only count submissions.</li>
        <li>Store your postal code or send anything about you to an AI service.</li>
      </ul>
    </article>
  );
}
