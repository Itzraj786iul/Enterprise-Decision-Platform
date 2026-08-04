type ComingSoonProps = {
  pageName: string;
};

/**
 * Route placeholder rendered inside the application shell.
 */
export function ComingSoon({ pageName }: ComingSoonProps) {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-2 py-16 text-center">
      <h1 className="text-2xl font-semibold tracking-tight text-foreground">{pageName}</h1>
      <p className="text-base text-muted-foreground">Coming Soon</p>
    </div>
  );
}
