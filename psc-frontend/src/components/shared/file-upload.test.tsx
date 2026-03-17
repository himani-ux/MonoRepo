/**
 * Tests for FEAT-INS-002/FEAT-CAR-003 upload validation behavior.
 *
 * PRD Reference: Docs/PRD.md Section 2.1 - FEAT-INS-002
 * PRD Reference: Docs/PRD.md Section 2.3 - FEAT-CAR-003
 */

import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { FileUpload } from './file-upload';

function makeFile(name: string, type: string, bytes: number): File {
  const content = new Uint8Array(bytes);
  return new File([content], name, { type });
}

describe('FileUpload', () => {
  it('test_feat_ins_002_accepts_valid_pdf_file_and_emits_onchange', () => {
    const onChange = vi.fn();
    const { container } = render(<FileUpload onChange={onChange} />);

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = makeFile('report.pdf', 'application/pdf', 1024);

    fireEvent.change(input, { target: { files: [file] } });

    expect(onChange).toHaveBeenCalledWith(file);
  });

  it('test_feat_car_003_rejects_invalid_file_type_with_error_message', () => {
    const onChange = vi.fn();
    const { container } = render(<FileUpload onChange={onChange} />);

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = makeFile('malware.exe', 'application/x-msdownload', 100);

    fireEvent.change(input, { target: { files: [file] } });

    expect(onChange).not.toHaveBeenCalled();
    expect(
      screen.getByText('Invalid file type. Only PDF and JPG/JPEG files are allowed.')
    ).toBeInTheDocument();
  });

  it('test_feat_car_003_rejects_oversize_file_greater_than_3mb', () => {
    const onChange = vi.fn();
    const { container } = render(<FileUpload onChange={onChange} />);

    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = makeFile('large.pdf', 'application/pdf', 3 * 1024 * 1024 + 1);

    fireEvent.change(input, { target: { files: [file] } });

    expect(onChange).not.toHaveBeenCalled();
    expect(screen.getByText('File size must not exceed 3.0 MB.')).toBeInTheDocument();
  });

  it('test_feat_ins_002_remove_file_emits_null_to_clear_selection', () => {
    const onChange = vi.fn();
    const file = makeFile('evidence.jpg', 'image/jpeg', 5000);

    render(<FileUpload onChange={onChange} value={file} />);
    fireEvent.click(screen.getByRole('button', { name: /remove file/i }));

    expect(onChange).toHaveBeenCalledWith(null);
  });
});

