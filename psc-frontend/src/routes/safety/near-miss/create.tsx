import { useNavigate } from "react-router-dom";

import { SafetyNearMissForm } from "../../../components/safety/near-miss/near-miss-form";
import { useToast } from "../../../hooks/use-toast";
import { getErrorMessage } from "../../../lib/api/client";
import { safetyApi } from "../../../lib/api/safety";
import type { SafetyNearMissSubmitValues } from "../../../schemas/safety/near-miss";

export default function SafetyNearMissCreatePage() {
  const navigate = useNavigate();
  const { toast } = useToast();

  async function handleSubmit(values: SafetyNearMissSubmitValues) {
    try {
      const nearMiss = await safetyApi.createNearMiss(values);
      toast({
        title: "Near miss created successfully",
        description: "The near miss record has been refreshed and opened.",
        variant: "success",
      });
      navigate(`/safety/near-miss/${nearMiss.public_id ?? nearMiss.id}`, {
        state: { resultMessage: "Near miss created successfully." },
      });
    } catch (error) {
      toast({
        title: "Unable to submit near miss",
        description: getErrorMessage(error),
        variant: "destructive",
      });
    }
  }

  return <SafetyNearMissForm onSubmit={handleSubmit} />;
}
