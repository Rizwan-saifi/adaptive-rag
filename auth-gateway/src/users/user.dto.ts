import { IsNotEmpty, IsString, Matches, MaxLength, MinLength } from 'class-validator';

// Rules for new accounts. Existing accounts may predate them, so login only caps lengths.
export class CreateUserDto {
  @IsString()
  @Matches(/^[A-Za-z0-9_.-]{3,32}$/, {
    message: 'username must be 3-32 characters: letters, digits, "_", "." or "-"',
  })
  username: string;

  @IsString()
  @MinLength(8)
  @MaxLength(128)
  password: string;
}

export class LoginDto {
  @IsString()
  @IsNotEmpty()
  @MaxLength(64)
  username: string;

  @IsString()
  @IsNotEmpty()
  @MaxLength(128)
  password: string;
}
