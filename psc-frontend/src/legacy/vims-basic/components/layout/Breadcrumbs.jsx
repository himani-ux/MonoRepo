import { Link, useLocation } from "react-router-dom";
import { generateBreadcrumbs } from "../../utils/breadcrumbs";

const Breadcrumbs = () => {
  const { pathname } = useLocation();
  const breadcrumbs = generateBreadcrumbs(pathname);

  if (!breadcrumbs.length) return null;

  return (
    <div className="bg-white px-4 py-2 border-b text-sm">
      {breadcrumbs.map((crumb, index) => (
        <span key={index}>
          {index !== breadcrumbs.length - 1 ? (
            <>
              <Link
                to={crumb.path}
                className="text-blue-600 hover:underline"
              >
                {crumb.label}
              </Link>
              <span className="mx-2">/</span>
            </>
          ) : (
            <span className="font-medium text-gray-700">
              {crumb.label}
            </span>
          )}
        </span>
      ))}
    </div>
  );
};

export default Breadcrumbs;
