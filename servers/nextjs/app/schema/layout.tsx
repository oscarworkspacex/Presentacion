import { ReactNode } from "react";
import { LayoutProvider } from "../(presentation-generator)/context/LayoutContext";

export default function SchemaLayout({
  children,
}: {
  children: ReactNode;
}) {
  return <LayoutProvider>{children}</LayoutProvider>;
}
