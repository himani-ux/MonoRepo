const CIRCULAR_FILE_BASE_URL = "";

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
        return `${CIRCULAR_FILE_BASE_URL}${normalizedPath}`;
    }

    return `${CIRCULAR_FILE_BASE_URL}/${normalizedPath}`;
};
