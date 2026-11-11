export function Placeholder({ title, message = "Coming soon." }: { title: string; message?: string }) {
  return (
    <div className="mx-auto max-w-3xl">
      <h1 className="text-3xl font-bold">{title}</h1>
      <p className="mt-2 text-muted-foreground">{message}</p>
    </div>
  );
}
