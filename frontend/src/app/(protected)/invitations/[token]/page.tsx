import { InvitationPage } from "@/features/workspaces/views";
export default async function Page({ params }: { params: Promise<{ token: string }> }) { const { token } = await params; return <InvitationPage key={token} token={token} />; }
