import { apiClient } from '@/lib/apiClient';

export async function GET() {
  try {
    const response = await apiClient.get('/health');
    return Response.json(response.data);
  } catch (error) {
    return Response.json({ status: 'error' }, { status: 500 });
  }
}