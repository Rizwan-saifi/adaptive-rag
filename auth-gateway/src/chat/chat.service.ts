import { BadGatewayException, GatewayTimeoutException, Injectable, Logger } from '@nestjs/common';
import { config } from '../config';

interface PythonResponse {
  result?: { content?: string; type?: string };
}

@Injectable()
export class ChatService {
  private readonly logger = new Logger(ChatService.name);

  async ask(query: string, conversationId: string, jwt: string): Promise<string> {
    this.logger.log(`Sending request to Python service (conversation ${conversationId})`);

    let resp: Response;
    try {
      resp = await fetch(config.pythonRagUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${jwt}` },
        body: JSON.stringify({ query, conversation_id: conversationId }),
        signal: AbortSignal.timeout(config.ragTimeout * 1000),
      });
    } catch (e) {
      if (e instanceof DOMException && e.name === 'TimeoutError') {
        throw new GatewayTimeoutException('The RAG service took too long to answer');
      }
      this.logger.error(`Failed to contact Python service: ${e}`);
      throw new BadGatewayException('Could not reach the RAG service');
    }
    if (!resp.ok) {
      this.logger.error(`Python service returned ${resp.status}: ${await resp.text()}`);
      throw new BadGatewayException(`RAG service returned an error (${resp.status})`);
    }

    let data: PythonResponse;
    try {
      data = (await resp.json()) as PythonResponse;
    } catch (e) {
      throw new BadGatewayException(`Invalid response from the RAG service: ${e}`);
    }
    if (data.result?.type !== 'ai' || typeof data.result.content !== 'string') {
      throw new BadGatewayException('Unexpected response from the RAG service');
    }
    return data.result.content;
  }
}
