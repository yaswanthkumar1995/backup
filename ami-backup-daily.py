import boto3
import collections
import datetime 
#By the time I used this script, the Lamda is not available in Mumbai region. So, I chosen Singapore region.
#Specify the region in which EC2 Instances located and to create AMI's. Ex: Mumbai region (ap-south-1)
ec = boto3.client('ec2', 'ap-south-1')
#ec = boto3.client('ec2')
def lambda_handler(event, context):        
    reservations = ec.describe_instances(        
        Filters=[            
            {'Name': 'tag-key', 'Values': ['Backup']},            
            { 'Name': 'instance-state-name','Values': ['running'] }        
        ]         
         ).get(        
        'Reservations', []    
    )        
    instances = sum(        
        [            
            [i for i in r['Instances']]            
            for r in reservations        
        ], [])    
    print("Found %d instances that need backing up" % len(instances))           
    
    to_tag = collections.defaultdict(list)    
    for instance in instances:        
        print("Instance name:" + [res['Value'] for res in instance['Tags'] if res['Key'] == 'Name'][0])                
        #Default retention for 7 days if the tag is not specified        
        try:            
            retention_days = [                
                int(t.get('Value')) for t in instance['Tags']                
                if t['Key'] == 'Retention'][0]        
        except IndexError:            
            retention_days = 7        
        except ValueError:            
            retention_days = 7        
        except Exception as e:                
            retention_days = 7                
        finally:                    
            create_time = datetime.datetime.now()            
            #create_fmt = create_time.strftime('%d-%m-%Y')            
            create_fmt = create_time.strftime('%d-%m-%Y')                
            try:                
                #Check for instance in running state               
                # if(ec.describe_instance_status(InstanceIds=[instance['InstanceId']],Filters=[{ 'Name': 'instance-state-name','Values': ['running'] }])['InstanceStatuses'][0]['InstanceState']['Name'] == 'running'):                                        
                #To make sure instance NoReboot enabled and to name the AMI                                
                AMIid = ec.create_image(InstanceId=instance['InstanceId'], Name="Lambda - " + [result['Value'] for result in instance['Tags'] if result['Key'] == 'Name'][0] + " - " + " From " + create_fmt, Description="Lambda created AMI of instance " + instance['InstanceId'], NoReboot=True, DryRun=False)                
                to_tag[retention_days].append(AMIid['ImageId'])                
                print("Retaining AMI %s of instance %s for %d days" % (                        
                    AMIid['ImageId'],                        
                    instance['InstanceId'],                        
                    retention_days,                    
                    ))                                
                    
                for retention_days in list(to_tag.keys()):                    
                    delete_date = datetime.date.today() + datetime.timedelta(days=retention_days)                    
                    delete_fmt = delete_date.strftime('%d-%m-%Y')                    
                    print("Will delete %d AMIs on %s" % (len(to_tag[retention_days]), delete_fmt))                                        
                    #To create a tag to an AMI when it can be deleted after retention period expires                    
                    ec.create_tags(                        
                        Resources=to_tag[retention_days],                        
                        Tags=[                            
                            {'Key': 'DeleteOn', 'Value': delete_fmt},                            
                            ]                        
                        )            
            #If the instance is not in running state                    
            except IndexError as e:                
                print("Unexpected error, instance "+[res['Value'] for res in instance['Tags'] if res['Key'] == 'Name'][0]+"-"+"\""+instance['InstanceId']+"\""+" might be in the state other then 'running'. So, AMI creation skipped.")  
