/** UI Components */

import React from 'react'
import MUIButton, { ButtonProps as MUIButtonProps } from '@mui/material/Button'
import MUIInput, { InputProps as MUIInputProps } from '@mui/material/TextField'
import MUICard, { CardProps as MUICardProps } from '@mui/material/Card'
import MUICardContent, { CardContentProps as MUICardContentProps } from '@mui/material/CardContent'
import MUITable, { TableProps as MUITableProps } from '@mui/material/Table'
import MUITableBody, { TableBodyProps as MUITableBodyProps } from '@mui/material/TableBody'
import MUITableCell, { TableCellProps as MUITableCellProps } from '@mui/material/TableCell'
import MUITableContainer, { TableContainerProps as MUITableContainerProps } from '@mui/material/TableContainer'
import MUITableHead, { TableHeadProps as MUITableHeadProps } from '@mui/material/TableHead'
import MUITableRow, { TableRowProps as MUITableRowProps } from '@mui/material/TableRow'
import MUIPaper, { PaperProps as MUIPaperProps } from '@mui/material/Paper'
import MUIBox, { BoxProps as MUIBoxProps } from '@mui/material/Box'
import MUITypography, { TypographyProps as MUITypographyProps } from '@mui/material/Typography'
import MUIChip, { ChipProps as MUIChipProps } from '@mui/material/Chip'
import MUIGrid from '@mui/material/Grid'
import MUIContainer from '@mui/material/Container'
import MUIAppBar from '@mui/material/AppBar'
import MUIToolbar, { ToolbarProps as MUIToolbarProps } from '@mui/material/Toolbar'
import MUIIconButton, { IconButtonProps as MUIIconButtonProps } from '@mui/material/IconButton'
import MUIDrawer, { DrawerProps as MUIDrawerProps } from '@mui/material/Drawer'
import MUIList, { ListProps as MUIListProps } from '@mui/material/List'
import MUIListItem, { ListItemProps as MUIListItemProps } from '@mui/material/ListItem'
import MUIListItemButton, { ListItemButtonProps as MUIListItemButtonProps } from '@mui/material/ListItemButton'
import MUIListItemIcon, { ListItemIconProps as MUIListItemIconProps } from '@mui/material/ListItemIcon'
import MUIListItemText, { ListItemTextProps as MUIListItemTextProps } from '@mui/material/ListItemText'
import MUIAvatar, { AvatarProps as MUIAvatarProps } from '@mui/material/Avatar'
import MUICircularProgress, { CircularProgressProps as MUICircularProgressProps } from '@mui/material/CircularProgress'
import MUIAlert, { AlertProps as MUIAlertProps } from '@mui/material/Alert'
import MUISnackbar, { SnackbarProps as MUISnackbarProps } from '@mui/material/Snackbar'
import MUISwitch, { SwitchProps as MUISwitchProps } from '@mui/material/Switch'
import MUIFormControlLabel, { FormControlLabelProps as MUIFormControlLabelProps } from '@mui/material/FormControlLabel'
import MUIBadge, { BadgeProps as MUIBadgeProps } from '@mui/material/Badge'

// Button
export interface ButtonProps extends MUIButtonProps {
  variant?: 'contained' | 'outlined' | 'text'
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning'
  size?: 'small' | 'medium' | 'large'
  loading?: boolean
}

export const Button: React.FC<ButtonProps> = ({ 
  children, 
  variant = 'contained', 
  color = 'primary',
  loading = false,
  disabled,
  ...props 
}) => (
  <MUIButton 
    variant={variant} 
    color={color}
    disabled={disabled || loading}
    {...props}
  >
    {loading ? <MUICircularProgress size={20} sx={{ mr: 1 }} /> : null}
    {children}
  </MUIButton>
)

// Input
export interface InputProps extends MUIInputProps {
  label?: string
  error?: boolean
  helperText?: string
}

export const Input: React.FC<InputProps> = ({ 
  label, 
  error = false, 
  helperText,
  ...props 
}) => (
  <MUIInput
    label={label}
    error={error}
    helperText={helperText}
    variant="outlined"
    fullWidth
    {...props}
  />
)

// Card
export interface CardProps extends MUICardProps {
  title?: string
  action?: React.ReactNode
}

export const Card: React.FC<CardProps> = ({ 
  children, 
  title,
  action,
  ...props 
}) => (
  <MUICard {...props}>
    {(title || action) && (
      <MUICardContent sx={{ pb: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        {title && <MUITypography variant="h6" component="h2">{title}</MUITypography>}
        {action}
      </MUICardContent>
    )}
    <MUICardContent>{children}</MUICardContent>
  </MUICard>
)

// Table
export interface TableColumn {
  key: string
  label: string
  render?: (row: Record<string, unknown>) => React.ReactNode
}

export interface TableProps {
  columns: TableColumn[]
  data: Record<string, unknown>[]
  onRowClick?: (row: Record<string, unknown>) => void
}

export const Table: React.FC<TableProps> = ({ columns, data, onRowClick }) => (
  <MUITableContainer component={MUIPaper}>
    <MUITable>
      <MUITableHead>
        <MUITableRow>
          {columns.map((col) => (
            <MUITableCell key={col.key}>{col.label}</MUITableCell>
          ))}
        </MUITableRow>
      </MUITableHead>
      <MUITableBody>
        {data.map((row, idx) => (
          <MUITableRow 
            key={idx} 
            hover={!!onRowClick}
            onClick={() => onRowClick?.(row)}
            sx={{ cursor: onRowClick ? 'pointer' : 'default' }}
          >
            {columns.map((col) => (
              <MUITableCell key={col.key}>
                {col.render ? col.render(row) : String(row[col.key] || '')}
              </MUITableCell>
            ))}
          </MUITableRow>
        ))}
      </MUITableBody>
    </MUITable>
  </MUITableContainer>
)

// Badge
export const Badge: React.FC<MUIBadgeProps> = (props) => <MUIBadge {...props} />

// Chip
export const Chip: React.FC<MUIChipProps> = (props) => <MUIChip {...props} />

// Typography
export const Typography: React.FC<MUITypographyProps> = (props) => <MUITypography {...props} />

// Box
export const Box: React.FC<MUIBoxProps> = (props) => <MUIBox {...props} />

// Paper
export const Paper: React.FC<MUIPaperProps> = (props) => <MUIPaper {...props} />

// Grid
export const Grid = MUIGrid

// Container
export const Container = MUIContainer

// AppBar
export const AppBar = MUIAppBar

// Toolbar
export const Toolbar: React.FC<MUIToolbarProps> = (props) => <MUIToolbar {...props} />

// IconButton
export const IconButton: React.FC<MUIIconButtonProps> = (props) => <MUIIconButton {...props} />

// Drawer
export const Drawer: React.FC<MUIDrawerProps> = (props) => <MUIDrawer {...props} />

// List
export const List: React.FC<MUIListProps> = (props) => <MUIList {...props} />

// ListItem
export const ListItem: React.FC<MUIListItemProps> = (props) => <MUIListItem {...props} />

// ListItemButton
export const ListItemButton: React.FC<MUIListItemButtonProps> = (props) => <MUIListItemButton {...props} />

// ListItemIcon
export const ListItemIcon: React.FC<MUIListItemIconProps> = (props) => <MUIListItemIcon {...props} />

// ListItemText
export const ListItemText: React.FC<MUIListItemTextProps> = (props) => <MUIListItemText {...props} />

// Avatar
export const Avatar: React.FC<MUIAvatarProps> = (props) => <MUIAvatar {...props} />

// CircularProgress
export const CircularProgress: React.FC<MUICircularProgressProps> = (props) => <MUICircularProgress {...props} />

// Alert
export const Alert: React.FC<MUIAlertProps> = (props) => <MUIAlert {...props} />

// Snackbar
export const Snackbar: React.FC<MUISnackbarProps> = (props) => <MUISnackbar {...props} />

// Switch
export const Switch: React.FC<MUISwitchProps> = (props) => <MUISwitch {...props} />

// FormControlLabel
export const FormControlLabel: React.FC<MUIFormControlLabelProps> = (props) => <MUIFormControlLabel {...props} />

// Status Badge component
export const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const getStatusColor = () => {
    switch (status.toLowerCase()) {
      case 'filled':
      case 'active':
      case 'success':
        return 'success'
      case 'pending':
      case 'open':
        return 'warning'
      case 'cancelled':
      case 'rejected':
      case 'error':
        return 'error'
      default:
        return 'default'
    }
  }

  return <Chip label={status} color={getStatusColor() as MUIChipProps['color']} size="small" />
}

export default {
  Button,
  Input,
  Card,
  Table,
  Badge,
  Chip,
  Typography,
  Box,
  Paper,
  Grid,
  Container,
  AppBar,
  Toolbar,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Avatar,
  CircularProgress,
  Alert,
  Snackbar,
  Switch,
  FormControlLabel,
  StatusBadge,
}
