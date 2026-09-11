export interface AdminConfirmationBubbleProps {
  targetInterfaceId: string | null;
  onAction: (approve: boolean) => void;
}
