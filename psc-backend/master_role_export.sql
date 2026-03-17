BEGIN TRANSACTION;

IF OBJECT_ID(N'dbo.master_role', N'U') IS NULL
BEGIN
  CREATE TABLE [dbo].[master_role] (
    [id] UNIQUEIDENTIFIER NOT NULL,
    [role_name] VARCHAR(100) NULL,
    [is_active] BIT NULL,
    [is_deleted] BIT NULL,
    [created_by] VARCHAR(100) NULL,
    [created_date] DATETIME NULL,
    [updated_by] VARCHAR(100) NULL,
    [updated_date] DATETIME NULL
    ,CONSTRAINT [PK_master_role] PRIMARY KEY ([id])
  );
END;

DELETE FROM [master_role];

INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'F415D39C-4037-EE11-B023-782B4610C006', N'Operation Team', 1, 1, NULL, '2023-08-10 11:11:55.357', NULL, '2024-05-27 16:12:33.890');
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'9EC9FB38-95CD-EF11-AA02-9ACA9A39E86D', N'Observer', 1, 0, NULL, '2025-01-08 13:20:27.160', NULL, NULL);
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'841C6054-A5D1-EF11-AA02-9ACA9A39E86D', N'Purchase Executive', 1, 0, NULL, '2025-01-13 17:26:45.343', NULL, NULL);
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'A103B023-A6D1-EF11-AA02-9ACA9A39E86D', N'Purchase Manager', 1, 0, NULL, '2025-01-13 17:31:37.527', NULL, NULL);
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'4BB2B3F3-D1B8-ED11-99AD-9DA677DD1A69', N'Test_New', 1, 1, NULL, '2023-03-02 08:12:20.463', NULL, '2024-05-27 16:12:28.233');
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'7195F6AF-87C4-ED11-99AD-9DA677DD1A69', N'Operational Section', 1, 1, NULL, '2023-07-29 12:44:09.840', NULL, '2024-05-27 16:12:38.443');
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'C9840F10-88C4-ED11-99AD-9DA677DD1A69', N'Change Request', 1, 1, NULL, '2023-03-17 05:53:39.240', NULL, '2024-05-27 16:12:43.583');
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'B4DD2C54-88C4-ED11-99AD-9DA677DD1A69', N'View_Only', 1, 1, NULL, '2023-03-17 05:55:33.517', NULL, '2024-05-27 16:12:48.323');
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'53718017-E8A2-ED11-B6BB-A864F15C6E2F', N'admin', 1, 0, NULL, '2024-05-27 15:29:16.770', NULL, '2025-02-10 15:39:48.887');
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'AEA9911E-E8A2-ED11-B6BB-A864F15C6E2F', N'Fleet Manager', 1, 0, NULL, '2024-05-27 16:04:17.670', NULL, '2024-05-27 15:25:58.820');
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'09F8D8F5-1FA6-ED11-B6BC-A864F15C6E2F', N'New Request', 1, 1, NULL, '2023-02-06 18:42:52.717', NULL, '2024-05-27 16:12:52.680');
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'26D5AD8F-83E3-EF11-AA04-CD8DB15AC468', N'Accounts', 1, 0, NULL, '2025-02-05 11:09:27.250', NULL, NULL);
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'C9CA60A5-9C20-EE11-99AE-DA75F524456D', N'SupportTeam', 1, 1, NULL, '2023-07-12 15:42:46.660', NULL, '2024-05-27 16:12:57.420');
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'37CD227D-4A0B-EE11-B6AD-DC1BA160DAFA', N'Developer', 1, 1, NULL, '2023-06-15 12:31:45.997', NULL, '2024-05-27 16:13:15.117');
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'2ABCE8A3-4A0B-EE11-B6AD-DC1BA160DAFA', N'Tester', 1, 1, NULL, '2023-06-15 12:32:51.047', NULL, '2024-05-27 16:13:20.230');
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'87F245A9-0CF2-F011-9DE1-DD0679876776', N'Technical Manager', 1, 0, NULL, '2026-01-15 17:51:05.193', NULL, NULL);
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'1BAAA9B0-0C1C-EF11-A9F1-F348983BAE6B', N'Super Admin', 1, 0, NULL, '2024-05-27 15:07:11.093', NULL, NULL);
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'30723F07-0F1C-EF11-A9F1-F348983BAE6B', N'Fleet_Manager', 1, 1, NULL, '2024-05-27 16:01:17.570', NULL, '2024-05-27 16:13:26.733');
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'D604980F-0F1C-EF11-A9F1-F348983BAE6B', N'Technical Superintendent', 1, 0, NULL, '2024-05-27 15:26:38.467', NULL, NULL);
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'407EF017-0F1C-EF11-A9F1-F348983BAE6B', N'Marine Superintendent', 1, 0, NULL, '2024-05-27 15:26:49.567', NULL, NULL);
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'809C3C1E-0F1C-EF11-A9F1-F348983BAE6B', N'SEQ Manager', 1, 0, NULL, '2024-05-27 15:24:33.920', NULL, NULL);
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'A446E624-0F1C-EF11-A9F1-F348983BAE6B', N'Crewing Manager', 1, 0, NULL, '2024-05-27 15:24:45.087', NULL, NULL);
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'0C3AD72B-0F1C-EF11-A9F1-F348983BAE6B', N'Crewing Executive', 1, 0, NULL, '2024-05-27 15:24:56.730', NULL, NULL);
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'AD92A33D-191C-EF11-A9F1-F348983BAE6B', N'Energy Efficiency and Operations Officer', 1, 0, NULL, '2024-05-27 16:37:01.557', NULL, NULL);
INSERT INTO [master_role] ([id], [role_name], [is_active], [is_deleted], [created_by], [created_date], [updated_by], [updated_date]) VALUES (N'28D37C55-191C-EF11-A9F1-F348983BAE6B', N'Senior Technical Superintendent', 0, 1, NULL, '2024-05-27 16:37:41.587', NULL, NULL);

COMMIT;
