import { WorkspaceDetail } from "@/features/workspaces/views";
export default async function Page({ params }: { params: Promise<{ workspaceId: string }> }) { const { workspaceId } = await params; return <WorkspaceDetail key={workspaceId} id={workspaceId} />; }
