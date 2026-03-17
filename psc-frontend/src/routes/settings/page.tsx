/**
 * Settings Page — Company Configuration
 *
 * Office users can upload company logo for PDF reports.
 * Vessel master users see a read-only view.
 */

import { useState, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, ImageIcon, Loader2, CheckCircle } from 'lucide-react';
import { RootLayout } from '@/components/layout/root-layout';
import { PageHeader } from '@/components/layout/page-header';
import { Card, CardContent, Button, Badge } from '@/components/ui';
import { useAuth } from '@/hooks/use-auth';
import { useToast } from '@/hooks/use-toast';
import { getCompanyLogo, uploadCompanyLogo } from '@/lib/api/settings';
import { API_BASE_URL } from '@/lib/utils/constants';

export default function SettingsPage() {
  const { isOffice } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);

  const { data: logoStatus, isLoading } = useQuery({
    queryKey: ['company-logo'],
    queryFn: getCompanyLogo,
    staleTime: 5 * 60 * 1000,
  });

  const uploadMutation = useMutation({
    mutationFn: uploadCompanyLogo,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['company-logo'] });
      setPreview(null);
      toast({
        title: 'Logo Uploaded',
        description: 'Company logo has been updated successfully.',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Upload Failed',
        description: error.message || 'Failed to upload company logo.',
        variant: 'destructive',
      });
    },
  });

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate type
    if (!['image/png', 'image/jpeg', 'image/jpg'].includes(file.type)) {
      toast({
        title: 'Invalid File',
        description: 'Logo must be PNG or JPG format.',
        variant: 'destructive',
      });
      return;
    }

    // Validate size (2MB)
    if (file.size > 2 * 1024 * 1024) {
      toast({
        title: 'File Too Large',
        description: 'Logo file must be under 2MB.',
        variant: 'destructive',
      });
      return;
    }

    // Show preview and upload
    const reader = new FileReader();
    reader.onloadend = () => setPreview(reader.result as string);
    reader.readAsDataURL(file);

    uploadMutation.mutate(file);
  };

  const logoUrl = logoStatus?.has_logo && logoStatus.logo_url
    ? `${API_BASE_URL}${logoStatus.logo_url}`
    : null;

  return (
    <RootLayout>
      <PageHeader title="Settings" />

      <div className="space-y-6">
        {/* Company Logo Section */}
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-base font-semibold text-neutral-900">
                  Company Logo
                </h3>
                <p className="mt-1 text-sm text-neutral-500">
                  This logo appears on PDF reports. Accepts PNG or JPG, max 2MB.
                </p>
              </div>
              {logoStatus?.has_logo && (
                <Badge variant="outline" className="text-success-600 border-success-300 bg-success-50">
                  <CheckCircle className="mr-1 h-3 w-3" />
                  Uploaded
                </Badge>
              )}
            </div>

            <div className="mt-4 flex items-center gap-6">
              {/* Logo preview */}
              <div className="flex h-24 w-48 items-center justify-center overflow-hidden rounded-lg border-2 border-dashed border-neutral-300 bg-neutral-50">
                {isLoading ? (
                  <Loader2 className="h-6 w-6 animate-spin text-neutral-400" />
                ) : preview ? (
                  <img
                    src={preview}
                    alt="Logo preview"
                    className="h-full w-full object-contain p-2"
                  />
                ) : logoUrl ? (
                  <img
                    src={logoUrl}
                    alt="Company logo"
                    className="h-full w-full object-contain p-2"
                  />
                ) : (
                  <div className="text-center">
                    <ImageIcon className="mx-auto h-8 w-8 text-neutral-300" />
                    <p className="mt-1 text-xs text-neutral-400">No logo</p>
                  </div>
                )}
              </div>

              {/* Upload button — office users only */}
              {isOffice && (
                <div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/png,image/jpeg,image/jpg"
                    className="hidden"
                    onChange={handleFileSelect}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploadMutation.isPending}
                  >
                    {uploadMutation.isPending ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <Upload className="mr-2 h-4 w-4" />
                    )}
                    {logoStatus?.has_logo ? 'Replace Logo' : 'Upload Logo'}
                  </Button>
                  <p className="mt-2 text-xs text-neutral-400">
                    PNG or JPG, max 2MB
                  </p>
                </div>
              )}

              {!isOffice && !logoStatus?.has_logo && (
                <p className="text-sm text-neutral-500">
                  Company logo can be uploaded by office users (DPA, SSQE, PIC).
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </RootLayout>
  );
}
