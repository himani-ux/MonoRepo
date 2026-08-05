import { apiClient } from './client';

export interface HelpChatContext {
  route?: string;
  module?: string;
  screen?: string;
  userRole?: string;
  vesselId?: string | null;
}

export interface HelpSource {
  id: string;
  title: string;
  module: string;
  source_path: string;
  score: number;
}

export interface HelpChatResponse {
  answer: string;
  sources: HelpSource[];
  retrieval_mode: 'qdrant' | 'local';
  llm_mode: 'configured' | 'not_configured' | 'error_fallback';
  suggested_questions: string[];
}

export interface HelpStatusResponse {
  documents_indexed: number;
  chunks_indexed: number;
  modules: Record<string, number>;
  qdrant_configured: boolean;
  embedding_configured: boolean;
  llm_configured: boolean;
  source: string;
}

export async function askHelpAssistant(
  question: string,
  context: HelpChatContext
): Promise<HelpChatResponse> {
  const response = await apiClient.post<HelpChatResponse>('/help/chat/', {
    question,
    context,
  });
  return response.data;
}

export async function getHelpSuggestions(
  context: HelpChatContext
): Promise<string[]> {
  const response = await apiClient.get<{ suggested_questions: string[] }>('/help/suggestions/', {
    params: {
      route: context.route,
      module: context.module,
      screen: context.screen,
    },
  });
  return response.data.suggested_questions;
}

export async function getHelpStatus(): Promise<HelpStatusResponse> {
  const response = await apiClient.get<HelpStatusResponse>('/help/status/');
  return response.data;
}
