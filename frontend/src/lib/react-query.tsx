import type { ReactNode } from "react";

export class QueryClient {}

export function QueryClientProvider({
  client,
  children,
}: {
  client: QueryClient;
  children: ReactNode;
}) {
  return <>{children}</>;
}

