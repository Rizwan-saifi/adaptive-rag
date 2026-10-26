import { IsNotEmpty, IsOptional, IsString, MaxLength } from 'class-validator';

export class ChatRequestDto {
  @IsString()
  @IsNotEmpty()
  @MaxLength(10000)
  query: string;

  // Which of the user's conversations the query belongs to
  @IsOptional()
  @IsString()
  @IsNotEmpty()
  @MaxLength(100)
  conversation_id?: string;
}
