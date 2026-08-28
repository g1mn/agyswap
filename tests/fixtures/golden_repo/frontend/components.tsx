/**
 * UI Components and Modal Dialogs.
 */

export interface ButtonProps {
  label: string;
  variant?: "primary" | "secondary" | "danger";
  disabled?: boolean;
  onClick: () => void;
}

export class ModalDialog {
  private isOpen: boolean = false;

  open(): void {
    this.isOpen = true;
  }

  close(): void {
    this.isOpen = false;
  }

  render() {
    return null;
  }
}

export function PrimaryButton(props: ButtonProps) {
  const { label, onClick, disabled = false } = props;
  return null;
}
