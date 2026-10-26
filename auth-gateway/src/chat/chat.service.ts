import { BadGatewayException, Injectable, InternalServerErrorException, Logger } from '@nestjs/common';
import { config } from '../config';

interface PythonResponse {
  result?: { content?: string; type?: string };
}

@Injectable()
export class ChatService {
  private readonly logger = new Logger(ChatService.name);

  async ask(query: string, jwt: string): Promise<string> {
    this.logger.log(`Sending request to Python service: ${query}`);

    let resp: Response;
    try {
      resp = await fetch(config.pythonRagUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${jwt}` },
        body: JSON.stringify({ query, session_id: jwt }),
      });
    } catch (e) {
      throw new InternalServerErrorException(`Failed to contact Python service: ${e}`);
    }
    if (!resp.ok) {
      throw new BadGatewayException('Python service returned an error');
    }

    let data: PythonResponse;
    try {
      data = (await resp.json()) as PythonResponse;
    } catch (e) {
      throw new InternalServerErrorException(`Failed to parse Python response: ${e}`);
    }
    if (data.result?.type === 'ai' && typeof data.result.content === 'string') {
      return data.result.content;
    }
    return 'No AI response found';
  }
}
