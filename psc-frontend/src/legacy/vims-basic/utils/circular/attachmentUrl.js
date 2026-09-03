import { API_BASE_URL } from '@/lib/utils/constants';

const DEFAULT_LOCAL_API_BASE_URL = "http://localhost:8000";

const getCircularFileBaseUrl = () => {
  const apiBaseUrl = API_BASE_URL.replace(/\/+$/, "");

  if (typeof window === "undefined") {
    return apiBaseUrl;
  }

  const currentOrigin = window.location.origin.replace(/\/+$/, "");
  const currentHost = window.location.hostname;

  if (
    apiBaseUrl === DEFAULT_LOCAL_API_BASE_URL &&
    currentHost !== "localhost" &&
    currentHost !== "127.0.0.1"
  ) {
    return "";
  }

  return apiBaseUrl === currentOrigin ? "" : apiBaseUrl;
};

export const buildCircularAttachmentUrl = (attachmentUrl) => {
  if (!attachmentUrl) {
    return "";
  }

  if (/^https?:\/\//i.test(attachmentUrl)) {
    return attachmentUrl;
  }

  const normalizedPath = attachmentUrl
    .replace(/^\/api\/circular(?=\/media\/)/i, "")
    .replace(/^\/+/, "/");

  if (normalizedPath.startsWith("/")) {
    return `${getCircularFileBaseUrl()}${normalizedPath}`;
  }

  return `${getCircularFileBaseUrl()}/${normalizedPath}`;
};
