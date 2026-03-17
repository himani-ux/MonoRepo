import { useAuth as useCoreAuth } from "@/hooks/use-auth";

export const useAuth = () => {
  const { user: authUser, isAuthenticated, tokens, isLoading } = useCoreAuth();
  const legacyUser = authUser
    ? {
        ...authUser,
        user_type: authUser.legacy_user_type ?? (authUser.user_type === "vessel" ? "ship" : "office"),
        display_name: authUser.display_name ?? authUser.full_name,
        role_name: authUser.role_name ?? authUser.role,
        username:
          authUser.username ??
          authUser.UserName ??
          authUser.login_id ??
          authUser.crew_id ??
          authUser.employee_id ??
          authUser.id,
        UserName:
          authUser.UserName ??
          authUser.username ??
          authUser.login_id ??
          authUser.crew_id ??
          authUser.employee_id ??
          authUser.id,
        work_side:
          authUser.work_side ??
          ((authUser.legacy_user_type ?? authUser.user_type) === "office" ? 0 : 1),
        first_name: authUser.first_name ?? "",
        surname: authUser.surname ?? "",
        is_chief: authUser.is_chief ?? false,
      }
    : null;

  const accessToken = tokens?.access ?? null;

  return { 
    isAuthenticated, 
    user: legacyUser, 
    accessToken,
    loading: isLoading,
  };
};
