import {RoleEnum} from "../enums/role.enum";

export class User {
  id: number;
  name: string;
  userName: string;
  email: string;
  password: string;
  authority: RoleEnum;
  accessToken: string;
  refreshToken: string;
  parameters: string;
  image: string;
}
