import { MODULES } from "../navigation/modules";

export const generateBreadcrumbs = (pathname) => {
  const crumbs = [];

  MODULES.forEach((module) => {
    if (pathname.startsWith(module.basePath)) {
      crumbs.push({
        label: module.label,
        path: module.basePath,
      });

      module.pages.forEach((page) => {
        const pagePathRegex = new RegExp(
          "^" + page.path.replace(/:\w+/g, "[^/]+") + "$"
        );

        if (pagePathRegex.test(pathname)) {
          crumbs.push({
            label: page.label,
            path: pathname,
          });
        }
      });
    }
  });

  return crumbs;
};
